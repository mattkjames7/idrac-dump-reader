def read_u16(data):
  low, high = data.next(2)
  return low | (high << 8)


def int_to_bool_array(value, length):
  return [bool(value & (1 << i)) for i in reversed(range(length))]


def signed_nibble(value):
  value = value & 0b1111
  out = value - 16 if value & 0b1000 else value
  return out


def bytes_to_guid(values):

  chars = []
  ranges = [
    [0,4],
    [4,6],
    [6,8],
    [8,10],
    [10,16]
  ]

  for i, rng in enumerate(ranges):
    for x in values[rng[0]:rng[1]]:
      chars.append(f"{x:02x}")
    if i < len(ranges) - 1:
      chars.append("-")
  return "".join(chars)
