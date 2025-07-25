from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS loans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_id INTEGER,
                  principal REAL,
                  period INTEGER,
                  interest_rate REAL,
                  total_amount REAL,
                  emi_amount REAL,
                  created_at TIMESTAMP,
                  remaining_amount REAL,
                  remaining_emis INTEGER,
                  FOREIGN KEY(customer_id) REFERENCES customers(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  loan_id INTEGER,
                  amount REAL,
                  payment_type TEXT,
                  payment_date TIMESTAMP,
                  FOREIGN KEY(loan_id) REFERENCES loans(id))''')
    
    conn.commit()
    conn.close()
init_db()

def get_db():
    conn = sqlite3.connect('bank.db')
    conn.row_factory = sqlite3.Row  
    return conn

@app.route('/loans', methods=['POST'])
def create_loan():
    data = request.json
    required_fields = ['customer_id', 'loan_amount', 'loan_period', 'interest_rate']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        customer_id = int(data['customer_id'])
        principal = float(data['loan_amount'])
        period = int(data['loan_period'])
        interest_rate = float(data['interest_rate'])
    except ValueError:
        return jsonify({'error': 'Invalid field types'}), 400

    interest = principal * period * interest_rate / 100
    total_amount = principal + interest
    emi_amount = total_amount / (period * 12)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Customer not found'}), 404
    
    c.execute('''INSERT INTO loans 
                 (customer_id, principal, period, interest_rate, total_amount, emi_amount, 
                  created_at, remaining_amount, remaining_emis)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (customer_id, principal, period, interest_rate, total_amount, emi_amount,
               datetime.now(), total_amount, period * 12))
    
    loan_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'loan_id': loan_id,
        'total_amount': round(total_amount, 2),
        'emi_amount': round(emi_amount, 2),
        'remaining_emis': period * 12
    }), 201

@app.route('/payments', methods=['POST'])
def make_payment():
    data = request.json
    required_fields = ['loan_id', 'amount', 'payment_type']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        loan_id = int(data['loan_id'])
        amount = float(data['amount'])
        payment_type = data['payment_type']
    except ValueError:
        return jsonify({'error': 'Invalid field types'}), 400
    
    if payment_type not in ['EMI', 'LUMP_SUM']:
        return jsonify({'error': 'Invalid payment type'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''SELECT remaining_amount, emi_amount, remaining_emis 
                 FROM loans WHERE id = ?''', (loan_id,))
    loan = c.fetchone()
    
    if not loan:
        conn.close()
        return jsonify({'error': 'Loan not found'}), 404
    
    remaining_amount = loan['remaining_amount']
    emi_amount = loan['emi_amount']
    remaining_emis = loan['remaining_emis']
    
    if payment_type == 'EMI' and amount < emi_amount:
        conn.close()
        return jsonify({'error': 'EMI payment must be at least the EMI amount'}), 400
    
    c.execute('''INSERT INTO payments 
                 (loan_id, amount, payment_type, payment_date)
                 VALUES (?, ?, ?, ?)''',
              (loan_id, amount, payment_type, datetime.now()))
    
    new_remaining = remaining_amount - amount
    
    if payment_type == 'EMI':
        new_emis = remaining_emis - 1
    else: 
        new_emis = int(new_remaining / emi_amount) if emi_amount > 0 else 0
        if new_remaining <= 0:
            new_remaining = 0
            new_emis = 0
    
    c.execute('''UPDATE loans 
                 SET remaining_amount = ?, remaining_emis = ?
                 WHERE id = ?''',
              (new_remaining, new_emis, loan_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'loan_id': loan_id,
        'amount_paid': amount,
        'remaining_amount': round(new_remaining, 2),
        'remaining_emis': new_emis
    }), 200

@app.route('/loans/<int:loan_id>/ledger', methods=['GET'])
def get_ledger(loan_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''SELECT remaining_amount, emi_amount, remaining_emis 
                 FROM loans WHERE id = ?''', (loan_id,))
    loan = c.fetchone()
    
    if not loan:
        conn.close()
        return jsonify({'error': 'Loan not found'}), 404
    
    c.execute('''SELECT amount, payment_type, payment_date 
                 FROM payments 
                 WHERE loan_id = ?
                 ORDER BY payment_date''', (loan_id,))
    payments = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'loan_id': loan_id,
        'remaining_amount': round(loan['remaining_amount'], 2),
        'emi_amount': round(loan['emi_amount'], 2),
        'remaining_emis': loan['remaining_emis'],
        'transactions': payments
    }), 200

@app.route('/customers/<int:customer_id>/loans', methods=['GET'])
def get_account_overview(customer_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Customer not found'}), 404
    
    c.execute('''SELECT 
                    l.id as loan_id,
                    l.principal,
                    l.total_amount,
                    l.emi_amount,
                    (l.total_amount - l.principal) as total_interest,
                    (l.total_amount - l.remaining_amount) as amount_paid,
                    l.remaining_emis
                 FROM loans l
                 WHERE l.customer_id = ?
                 ORDER BY l.created_at''', (customer_id,))
    
    loans = []
    for row in c.fetchall():
        loan = dict(row)
        loan['total_amount'] = round(loan['total_amount'], 2)
        loan['emi_amount'] = round(loan['emi_amount'], 2)
        loan['total_interest'] = round(loan['total_interest'], 2)
        loan['amount_paid'] = round(loan['amount_paid'], 2)
        loans.append(loan)
    
    conn.close()
    
    return jsonify({
        'customer_id': customer_id,
        'loans': loans
    }), 200

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.json
    if 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('INSERT INTO customers (name) VALUES (?)', (data['name'],))
    customer_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'customer_id': customer_id,
        'name': data['name']
    }), 201

if __name__ == '__main__':
    app.run(debug=True)
