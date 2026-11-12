from .raw_record_data import RawRecordData


def read_header(file_data):
  out = {}
  out["record_id"] = int.from_bytes([next(file_data), next(file_data)], byteorder="little")
  out["sdr_version"] = int.from_bytes([next(file_data)], byteorder="little")
  out["record_type"] = int.from_bytes([next(file_data)], byteorder="little")
  out["record_length"] = int.from_bytes([next(file_data)], byteorder="little")

  record_bytes = [next(file_data) for _ in range(out["record_length"])]
  return out, RawRecordData(record_bytes)
