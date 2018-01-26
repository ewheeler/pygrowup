"""
Usage: python munge_data.py

For each of the WHO data files, parse, translate, and save each out to a new
pure, importable Python data structure (a new module per file).
"""
import csv
from decimal import Decimal
from pprint import pprint

MALE = "1"
FEMALE = "2"


def parse_file(file_name):
    """Parse a CSV and return a data structure of its contents.
    CSV's header row should contain: sex, age (or height), l, m, s.

    Returns a dict like {
        "male": {
            1: {"l": Decimal(value), "m": Decimal(value), "s": Decimal(value)},
            2: {"l": Decimal(value), "m": Decimal(value), "s": Decimal(value)},
            etc,
            },
        "female": {
            1: {"l": Decimal(value), "m": Decimal(value), "s": Decimal(value)},
            2: {"l": Decimal(value), "m": Decimal(value), "s": Decimal(value)},
            etc,
            },
        }
    (The keys that are numbers represent "t": days or length/height.)

    Note that flags indicating "L" or "H" are dropped.
    """
    with open(file_name) as f:
        results = {
            "male": {},
            "female": {},
            }
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            sex = row["sex"]
            if "age" in row:
                t = int(row["age"])
            elif "height" in row:
                t = Decimal(row["height"])
            else:
                t = Decimal(row["length"])
            data = {
                "l": Decimal(row["l"]),
                "m": Decimal(row["m"]),
                "s": Decimal(row["s"]),
                }
            if sex == MALE:
                results["male"][t] = data
            elif sex == FEMALE:
                results["female"][t] = data
    return results


output_input = (
    ("acfa.py", "arm_circumference_for_age.txt"),
    ("bmifa.py", "bmi_for_age.txt"),
    ("hcfa.py", "head_circumference_for_age.txt"),
    ("lfa.py", "length_for_age.txt"),
    ("ssfa.py", "subscapular_skinfold_for_age.txt"),
    ("tsfa.py", "triceps_skinfold_for_age.txt"),
    ("wfa.py", "weight_for_age.txt"),
    ("wfh.py", "weight_for_height.txt"),
    ("wfl.py", "weight_for_length.txt"),
    )

template = """from decimal import Decimal

DATA = """

for out_fname, in_fname in output_input:
    parsed = parse_file(in_fname)
    with open("../%s" % out_fname, "w") as out_file:
        print(template, end="", file=out_file)
        pprint(parsed, stream=out_file)
