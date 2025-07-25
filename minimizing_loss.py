def minimize(prices):
  min_loss=float('inf')
  buy_year=sell_year=-1
  price_years=[(price, year+1) for year, price in enumerate(prices)]
  price_years.sort(reverse=True, key=lambda x:x[0])

  for i in range(len(price_years)-1):
    curr_price, curr_year=price_years[i]
    next_price, next_year=price_years[i+1]
    if next_year>curr_year:
      loss=curr_price-next_price
      if 0<loss<min_loss:
        min_loss=loss
        buy_year=curr_year
        sell_year=next_year
  return (buy_year, sell_year, min_loss)

print(minimize([100, 180, 260, 310, 40, 535, 695]))
