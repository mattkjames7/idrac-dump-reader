
def fru_device_locator_record_key_bytes(data):

  out = {}
  out["device_access_address"] = data.next()[0] >> 1

  # I think we need the following byte to define this one
  fru_address = data.next()[0]

  value = data.next()[0]
  out["fru_device_type"] = "logical" if value >> 7 else "physical"
  out["lun"] = (value & 0b0001_1000) >> 3
  out["bus_id"] = value & 0b0000_0111

  if out["fru_device_type"] == "logical":
    out["logical_fru_device"] = fru_address
  else:
    out["device_slave_address"] = fru_address >> 1

  out["channel_number"] = data.next()[0] >> 4

  return out


def fru_device_locator_body(data):

  out = {}

  # 10 - reserved
  _ = data.next()[0]

  # 11 - device type (from table 43-12)
  # 12 - device type modifier (from table 43-12)
  out["device_type"], out["device_modifier"] = device_type_code(data.next(2))

  # 13 - FRU entity id
  out["fru_entity_id"] = data.next()[0]

  # 14 - FRU entity instance
  out["fru_entity_instance"] = data.next()[0]

  # 15 - OEM
  _ = data.next()[0]

  # 16 onwards - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out
