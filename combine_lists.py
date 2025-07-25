def combine(list1, list2):
  combined=list1+list2
  combined.sort(key=lambda x:x['positions'][0])
  i=0
  while i<len(combined)-1:
    now=combined[i]
    next=combined[i+1]
    curr_left, curr_right=now['positions']
    next_left, next_right=next['positions']

    overlap=min(curr_right, next_right)-max(curr_left, next_left)
    cuurent_length=curr_right-curr_left
    next_length=next_right-next_left
    if overlap>current_length/2 or overlap>next_length/2:
      new_left=min(curr_left, next_left)
      new_right=max(curr_right, next_right)
      new_values=now['values']+next['values']
      combined[i]={
          'positions': [new_left, new_right],
          'values': new_values
      }
      del combined[i+1]
    else:
      i+=1
  return combined
