
def generic_device_locator_record_key_bytes(data):

  out = {}

  value = data.next()[0]
  address = value >> 0
  out["device_access_address"] = address
  out["on_ipmb"] = address == 0

  value  = data.next()[0]
  out["device_slave_address"] = value >> 1
  channel_msb = value & 0b1

  value = data.next()[0]
  out["channel_number"] = (channel_msb << 3) | (value >> 5)
  out["access_lun"] = (value & 0b0001_1000) >> 3
  out["bus_id"] = value & 0b0000_0111

  return out


def generic_device_locator_record_body(data):

  out = {}

  # 9 - address span
  out["address_span"] = data.next()[0] & 0b0000_0111  # ignore reserved bits

  # 10 - skip reserved
  _ = data.next()

  # 11 - device type (from table 43-12)
  # 12 - device type modifier (from table 43-12)
  out["device_type"], out["device_modifier"] = device_type_code(data.next(2))

  # 13 - entity id
  out["entity_id"] = data.next()[0]

  # 14 - entity instance
  out["entity_instance"] = data.next()[0]

  # 15 - OEM
  out["oem"] = data.next()[0]

  # 16 onward - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out
