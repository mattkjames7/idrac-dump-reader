def decode_bcd(str_bytes):

  char_map = {
    10: " ",
    11: "-",
    12: ".",
    13: ";",
    14: ",",
    15: "_"
  }

  out = ""
  for byte in str_bytes:
    upper = byte >> 4
    lower = byte & 0b00001111

    for part in [upper, lower]:
      out += char_map.get(part, f"{int(part)}")
  return out


def decode_6bit_ascii(str_bytes):

  chars = " !\"#$%&'()*+,-./0123456789:;<=>?"
  chars += "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"

  out = ""
  last = None
  remaining = 0
  for i, byte in enumerate(str_bytes):
    t = i % 3

    if t == 0:
      upper = byte >> 6
      remaining = upper
      lower = byte & 0b00111111
      out += chars[lower]
    elif t == 1:
      upper = byte >> 4
      lower = byte & 0b00001111
      index = (lower << 2) | remaining
      out += chars[index]
      remaining = upper
    else:
      upper = byte >> 2
      lower = byte & 0b00000011
      index = (lower << 4) | remaining
      out += chars[index]
      out += chars[upper]
  return out


def decode_8bit_ascii(str_bytes):

  return bytes(str_bytes).decode("latin-1")


def decode_unicode(str_bytes):

  return bytes(str_bytes).decode("utf-16-le")


def decode_device_id(data):

  value = data.next()[0]
  fmt_code = (value & 0b11000000) >> 6
  fmt = {
    0: "unicode",
    1: "bcd-plus",
    2: "6-bit-ascii",
    3: "8-bit-ascii"
  }[fmt_code]

  str_length = value & 0b00011111
  if fmt == "unicode":
    byte_length = str_length * 2
  elif fmt == "bcd-plus":
    byte_length = (str_length + 1) // 2
  elif fmt == "6-bit-ascii":
    byte_length = (str_length * 6 + 7) // 8
  else:
    byte_length = str_length

  device_id = None
  if not str_length in [0, 31]:
    str_bytes = data.next(byte_length)

    if fmt == "unicode":
      device_id = decode_unicode(str_bytes)
    elif fmt == "bcd-plus":
      device_id = decode_bcd(str_bytes)
    elif fmt == "6-bit-ascii":
      device_id = decode_6bit_ascii(str_bytes)
    else:
      device_id = decode_8bit_ascii(str_bytes)

  return fmt, device_id
