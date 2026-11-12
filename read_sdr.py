from records.header import read_header

fname = "sdr.bin"


def main():

  with open(fname, "rb") as f:
    file_data = iter(f.read())

  while True:
    try:
      record, record_data = read_header(file_data)
      if record["record_length"] == 0:
        break

      if record["record_type"] == 1:
        record.update(read_record_key_bytes(record_data))
        record.update(full_sensor_record_body_bytes(record_data))
      elif record["record_type"] == 2:
        record.update(read_compact_record_key_bytes(record_data))
        record.update(compact_sensor_record(record_data))
      print(record.get("device_id"), record.get("device_id_fmt"), record)
    except StopIteration:
      break


if __name__ == "__main__":
  main()
