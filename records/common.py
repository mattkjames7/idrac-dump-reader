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


def decode_raw(raw, format_value):

  negative = raw & 0b1000_000
  if format_value == "unsigned":
    return raw
  elif format_value == "signed, 1's complement":
    return -(~raw & 0b1111_1111) if negative else raw
  elif format_value == "signed, 2's complement":
    return raw - 256 if raw >= 128 else raw

  raise ValueError("This shouldn't really happen")


def raw_to_real_value(raw, M, B, B_exp, R_exp, format_value):

  x = decode_raw(raw, format_value)

  return (M * x + B * (10**B_exp)) * (10**R_exp)


def raw_converter(M, B, B_exp, R_exp, format_value):

  def convert(raw, convertable=True):
    if convertable:
      return raw_to_real_value(raw, M, B, B_exp, R_exp, format_value)
    else:
      return None

  return convert


def raw_hysteresis_converter(raw, M, R_exp):
  return raw * M * (10**R_exp)
