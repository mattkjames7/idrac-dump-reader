from .common import bytes_to_guid


def management_controller_confirmation_record_key_bytes(data):

  out = {}

  out["device_slave_adress"] = data.next()[0] >> 1
  out["device_id"] = data.next()[0]

  value = data.next()[0]
  out["channel_number"] = value >> 4
  out["device_revision"] = value & 0b0000_1111

  return out


def management_controller_confirmation_body(data):
  """Table 43-9, page 575"""
  out = {}

  # 9 - firmware major revision
  major = data.next()[0] & 0b0111_1111

  # 10 - firmware minor revision
  minor = data.next()[0]

  out["firmware_revision"] = f"{major}.{minor}"

  # 11 - IPMI version
  value = data.next()[0]
  lsd = value >> 4
  msd = value & 0b0000_1111
  out["ipmi_version"] = f"{msd}.{lsd}"

  # 12 - 14 - manufacturer id
  values = data.next(3)
  out["manufacturer_id"] = int(
    ((values[2] & 0b0000_1111) << 16)
    | (values[1] << 8)
    | values[0]
  )

  # 15 -16 - product id
  values = data.next(2)
  out["product_id"] = int((values[1] << 8) | values[0])

  # 17 - 32 - device guid
  out["device_guid"] = bytes_to_guid(data.next(16))

  return out


def management_controller_confirmation_record(data):

  out = management_controller_confirmation_record_key_bytes(data)
  out.update(management_controller_confirmation_body(data))

  return out
