def format(num):
  num_str="{:.4f}".format(num)
  int_part, deci_part=num_str.split('.') if '.' in num_str else (num_str, '00')

  length=len(int_part)
  if length<=3:
    formatted_int=int_part
  else:
    last=int_part[-3:]
    other=int_part[:-3]
    formatted_other=','.join([other[max(i-2, 0):i] for i in range(len(other), 0, -2)][::-1])
    formatted_int=f"{formatted_other}, {last}" if formatted_other else last
  return f"{formatted_int}.{deci_part}"

print(format(123456.78910))
