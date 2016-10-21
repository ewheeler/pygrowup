import csv
import json
import sys


# This is only tested in Python 3, but it shouldn't matter for typical use;
# it's just to convert the WHO's text files to JSON once and then it's done.
def convert_text2json(source_path, output_path=None):
    if not output_path:
        if source_path.endswith("_z_WHO2007_exp.txt"):
            prefix = "../../" + source_path.replace("_z_WHO2007_exp.txt", "")
            output_path = prefix + "_5_19_zscores.json"
        else:
            sys.exit("Unsure how to infer output_path; please specify one.")
    reader = csv.DictReader(open(source_path), delimiter="\t")
    data = [row for row in reader]
    with open(output_path, "w") as output:
        print(json.dumps(data), file=output)
    print("Done output to %s" % output_path)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("Error: expecting a source file path, and optionally, an "
                 "output file path")
    convert_text2json(*args)
