def caesar(msg, shift, mode='encode'):
  res=[]
  shift=shift%26
  for char in msg:
    if char.isalpha():
      base=ord('A') if char.isupper() else ord('a')
      if mode=='encode':
        new_char=chr((ord(char)-base+shift)%26 + base)
      else:
        new_char=chr((ord(char)-base-shift)%26 + base)
      res.append(new_char)
    else:
      res.append(char)
  return "".join(res)

print(caesar("Hello World", 3))
print(caesar('encode', 3, 'decode'))
