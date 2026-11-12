
def management_controller_device_record_key_bytes(data):

  out = {}

  out["device_slave_address"] = data.read()[0] >> 1

  out["channel_number"] = data.read()[0] & 0b1111

  return out


def management_controller_device_body(data):
  """table 43-8, page 573-574"""
  out = {}

  # 8 - power state notification / global initialization
  value = data.next()[0]
  out["power_state_notification"] = {
    "acpi_system": bool(value & 0b1000_0000),
    "acpi_device": bool(value & 0b0100_0000),
    "controller": bool(value & 0b0010_0000)
  }
  out["global_initialization"] = {
    "controller_logs_agent_error": bool(value & 0b0000_1000),
    "log_agent_access_error": bool(value & 0b0000_0100),
    "event_message_generation": {
      0: "enabled",
      1: "disabled",
      2: "controller_not_initialized"
    }.get(value & 0b0000_0011, "reserved")
  }

  # 9 - device capabilities
  value = data.next()[0]
  out["capabilities"] = {
    "chassis_device": bool(value & 0b1000_0000),
    "bridge": bool(value & 0b0100_0000),
    "ipmb_event_generator": bool(value & 0b0010_0000),
    "ipmb_event_receiver": bool(value & 0b0001_0000),
    "fru_inventory_device": bool(value & 0b0000_1000),
    "sel_device": bool(value & 0b0000_0100),
    "sdr_repository_device": bool(value & 0b0000_0010),
    "sensor_device": bool(value & 0b0000_0001)
  }

  # 10 - 12 - reserved
  _ = data.next(3)

  # 13 - entity id
  out["entity_id"] = data.next()[0]

  # 14 - entity instance
  out["entity_instance"] = data.next()[0]

  # 15 - OEM
  out["oem"] = data.next()[0]

  # 16 onwards - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out
