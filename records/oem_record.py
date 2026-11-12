

def oem_record(data, record_length):
  """Table 43-11, page 578"""

  man_id_bytes = data.next(3)
  man_id = (
      ((man_id_bytes[2] & 0x0f) << 16)
      | (man_id_bytes[1] << 8)
      | man_id_bytes[0]
  )
  out = {
    "manufacturer_id": f"{man_id:06x}",
    "data": data.next("all")
  }

  return out
