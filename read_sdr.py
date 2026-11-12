import json

from records.read_sdr_file import read_sdr_file

input_fname = "sdr.bin"
output_fname = "sdr.json"


def main():

  records = read_sdr_file(input_fname)

  with open(output_fname, "w") as f:
    json.dump(records, f, indent=2)


if __name__ == "__main__":
  main()
