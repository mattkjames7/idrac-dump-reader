from .read_record import read_record


def read_sdr_file(fname: str):

  records = []

  with open(fname, "rb") as f:
    file_data = iter(f.read())

    while True:
      try:
        records.append(read_record(file_data))
      except StopIteration:
        break

  return records
