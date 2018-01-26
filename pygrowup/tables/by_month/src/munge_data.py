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


def parse_files(file_names):
    """Parse a list of CSVs and return their combined data as a Python data
    structure.
    With a header row containing: sex, age (or height), l, m, s.

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
    results = {
        "male": {},
        "female": {},
        }
    for file_name in file_names:
        if "boy" in file_name:
            sex = "male"
        elif "girl" in file_name:
            sex = "female"
        else:
            raise Exception("Indeterminate sex for file '%s'" % file_name)
        with open(file_name) as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                t = int(row["Month"])
                data = {
                    "l": Decimal(row["L"]),
                    "m": Decimal(row["M"]),
                    "s": Decimal(row["S"]),
                    }
                results[sex][t] = data
    return results


# For ages (0-5) where we already have daily data, we ignore their monthly
# versions.
output_input = (
    ("acfa.py", (
        "mramba_acfa_boys_5_19.txt",
        "mramba_acfa_girls_5_19.txt",
        )
     ),
    ("bmifa.py", (
        # "bmi_boys_0_2_zcores.txt",
        # "bmi_boys_2_5_zscores.txt",
        "bmi_boys_z_WHO2007_exp.txt",
        # "bmi_girls_0_2_zscores.txt",
        # "bmi_girls_2_5_zscores.txt",
        "bmi_girls_z_WHO2007_exp.txt",
        )
     ),
    # ("hcfa.py", (
    #     "tab_hcfa_boys_z_0_5.txt",
    #     "tab_hcfa_girls_z_0_5.txt",
    #     )
    # ),
    ("lfa.py", (
        "hfa_boys_z_WHO2007_exp.txt",
        "hfa_girls_z_WHO2007_exp.txt",
        # "lhfa_boys_0_2_zscores.txt",
        # "lhfa_boys_2_5_zscores.txt",
        # "lhfa_girls_0_2_zscores.txt",
        # "lhfa_girls_2_5_zscores.txt",
        )
     ),
    # ("ssfa.py", (
    #     "tab_ssfa_boys_z_3_5.txt",
    #     "tab_ssfa_girls_z_3_5.txt",
    #     )
    # ),
    # ("tsfa.py", (
    #     "tab_tsfa_boys_z_3_5.txt",
    #     "tab_tsfa_girls_z_3_5.txt",
    #     )
    # ),
    ("wfa.py", (
        # "wfa_boys_0_5_zscores.txt",
        "wfa_boys_z_WHO2007_exp.txt",
        # "wfa_girls_0_5_zscores.txt",
        "wfa_girls_z_WHO2007_exp.txt",
        )
     ),
    # ("wfh.py", (
    #     "wfh_boys_2_5_zscores.txt",
    #     )
    # ),
    # ("wfl.py", (
    #     "wfl_boys_0_2_zscores.txt",
    #     )
    #  ),
    )

template = """from decimal import Decimal

DATA = """

for out_fname, in_fnames in output_input:
    parsed = parse_files(in_fnames)
    with open("../%s" % out_fname, "w") as out_file:
        print(template, end="", file=out_file)
        pprint(parsed, stream=out_file)
