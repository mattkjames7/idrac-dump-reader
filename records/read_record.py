from typing import Iterator

from .bmc_message_channel_info_record import bmc_message_channel_info_record
from .compact_sensor_record import compact_sensor_record
from .device_relative_entity_association_record import device_relative_entity_association_record
from .entity_association_record import entity_association_record
from .event_only_record import event_only_record
from .fru_device_locator_record import fru_device_locator_record
from .full_sensor_record import full_sensor_record
from .generic_device_locator_record import generic_device_locator_record
from .header import read_header
from .management_controller_confirmation_record import management_controller_confirmation_record
from .management_controller_device_record import management_controller_device_record
from .oem_record import oem_record


record_function_map = {
  0x01: full_sensor_record,
  0x02: compact_sensor_record,
  0x03: event_only_record,
  0x08: entity_association_record,
  0x09: device_relative_entity_association_record,
  0x10: generic_device_locator_record,
  0x11: fru_device_locator_record,
  0x12: management_controller_device_record,
  0x13: management_controller_confirmation_record,
  0x14: bmc_message_channel_info_record,
  0xc0: oem_record
}


def unknown_record(data):
  return {"note": "unknown record type"}


def read_record(file_data: Iterator):

  record, record_data = read_header(file_data)

  if record["record_length"] == 0:
    return record

  record_function = record_function_map.get(record["record_type"], unknown_record)
  record.update(record_function(record_data))
  print(record.get("record_id"), record.get("record_type"), record.get("device_id"))
  return record
