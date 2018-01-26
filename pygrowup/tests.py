import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import os
import os.path
try:
    # unittest2 is a dependency for Python < 3.4; after that subTests were
    # introduced to unittest
    import unittest2 as unittest
except ImportError:
    import unittest

from . import exceptions, Observation


DATASET_DIR = os.path.join(os.getcwd(), "pygrowup", "test_datasets")

# This file is derived from the R implementation of iGrowup. We're trusting
# its z-score values. It's a CSV with erratically named columns, so we
# normalize the names for ease of use.
TEST1_FILE_NAME = "MySurvey_z_st.csv"

# This file is derived from a sample set of data from SPOON, run through the
# stata implementation of iGrowup. We're trusting its z-score values as well.
# And it's also a CSV with erratically named columns, so we again normalize
# names for ease of use.
TEST2_FILE_NAME = "test_dataset.csv"

# How close do we want our results to match other's?
DELTA = 0.1

HEADER_MAP_1 = {
    "sex": 'GENDER',
    "head_circumference": 'HEAD',
    "height": 'HEIGHT',
    "arm_circumference": 'MUAC',
    # 'SUB',
    # 'SW',
    # 'TRI',
    "weight": 'WEIGHT',
    "age_in_days": 'age.days',
    "age_in_months": 'agemons',
    "bmi": 'cbmi',
    # 'clenhei',
    # 'fac',
    # 'fbmi',
    # 'fhc',
    # 'flen',
    # 'fss',
    # 'fts',
    # 'fwei',
    # 'fwfl',
    "id": 'id',
    "l_or_h": 'measure',
    # 'oedema',
    # 'region',
    "subscapular_skinfold": 'subskin',
    # 'sw',
    "triceps_skinfold": 'triskin',
    "acfa_z": 'zac',
    "bmifa_z": 'zbmi',
    "hcfa_z": 'zhc',
    "lfa_z": 'zlen',
    "ssfa_z": 'zss',
    "tsfa_z": 'zts',
    "wfa_z": 'zwei',
    "wfl_z": 'zwfl',
    }

HEADER_MAP_2 = {
    "sex": "sex",
    "dob": "dob",
    "age_in_months": "agemons",
    "head_circumference": "head",
    "lfa_z": "_zhfa",  # =/over 5
    # "_agemons",
    "lfa_z2": "_zlen",  # under 5
    "hcfa_z": "_zhc",
    "bmifa_z": "_zbfa",  # under 5
    # "gender",
    "id": "id",
    "date_of_observation": "screen_date",
    "wfa_z": "_zwfa",  # =/over 5
    "wfa_z2": "_zwei",  # under 5
    "bmifa_z2": "_zbmi",  # =/over 5
    "bmi": "_cbmi",
    "height": "height",
    "weight": "weight",
    "wfl_z": "_zwfl",
}

SEX_MAP = {
    "2": Observation.FEMALE,
    "1": Observation.MALE,
    }


def get_field_1(r, f, as_d=False):
    result = r[HEADER_MAP_1[f]]
    if as_d and result is not None and result != "":
        try:
            result = Decimal(result)
        except InvalidOperation:
            raise Exception("Invalid decimal input: '%s'" % result)
    return result


def get_field_2(r, f, as_d=False):
    # Some fields are split over two field names (one for children under 5, one
    # for over 5)
    k = HEADER_MAP_2[f]
    k2 = HEADER_MAP_2.get(f + "2")
    result = r.get(k) or r.get(k2)
    if as_d and result is not None and result != "":
        try:
            result = Decimal(result)
        except InvalidOperation:
            raise Exception("Invalid decimal input: '%s'" % result)
    return result


class TestZScores(unittest.TestCase):

    def perform_test_for_metric(self, y_name, z_name, method_name, msg, **kw):
        method_kwargs = kw.get("method_kwargs", {})
        method_kwargs2 = kw.get("method_kwargs2", {})
        filter_ = kw.get("filter_", None)
        filter2_ = kw.get("filter2_", None)
        test_both_files = kw.get("test_both_files", False)
        count = 0

        # First test the iGrowup data set
        file_name = os.path.join(DATASET_DIR, TEST1_FILE_NAME)
        with open(file_name) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Optional filter function to weed out rows that aren't
                # applicable for this test
                if filter_ and not filter_(row):
                    continue
                age_in_months = get_field_1(row, "age_in_months")
                y = get_field_1(row, y_name, as_d=True)
                theirs = get_field_1(row, z_name, as_d=True)
                if not y or theirs in (None, ""):
                    continue
                # These get reported back upon sub-test failure, to aid
                # troubleshooting.
                subtest_feedback = {
                    "id": row["id"],
                    "age_in_months": age_in_months,
                    "measurement": y,
                }
                with self.subTest(**subtest_feedback):
                    sex = SEX_MAP[get_field_1(row, "sex")]
                    if method_kwargs:
                        kwargs = {
                            # v assumed to be a callable
                            k: v(row) for k, v in method_kwargs.items()
                            }
                    else:
                        kwargs = {}

                    # Test based on day-level age granularity
                    obs_by_day = Observation(
                        sex=sex, age_in_days=get_field_1(row, "age_in_days")
                        )
                    method = getattr(obs_by_day, method_name)
                    ours_by_day = method(y, **kwargs)
                    self.assertAlmostEqual(ours_by_day, theirs, delta=DELTA)

                    # Retest with month-level age granularity
                    obs_by_month = Observation(
                        sex=sex, age_in_months=age_in_months
                        )
                    method = getattr(obs_by_month, method_name)
                    ours_by_month = method(y, **kwargs)
                    self.assertAlmostEqual(ours_by_month, theirs, delta=DELTA)

                    count += 1

        # Next (optionally) test the data set generated with Stata, which
        # contains a wider age range.
        if test_both_files:
            file_name = os.path.join(DATASET_DIR, TEST2_FILE_NAME)
            with open(file_name) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Optional filter function to weed out rows that aren't
                    # applicable for this test
                    if filter2_ and not filter2_(row):
                        continue
                    y = get_field_2(row, y_name, as_d=True)
                    theirs = get_field_2(row, z_name, as_d=True)
                    if not y or theirs in (None, ""):
                        continue
                    age_in_months = get_field_2(row, "age_in_months")
                    # These get reported back upon sub-test failure, to aid
                    # troubleshooting.
                    subtest_feedback = {
                        "id": row["id"],
                        "age_in_months": age_in_months,
                        "measurement": y,
                    }
                    with self.subTest(**subtest_feedback):
                        sex = get_field_2(row, "sex").lower()
                        if method_kwargs2:
                            kwargs = {
                                # v assumed to be a callable
                                k: v(row) for k, v in method_kwargs2.items()
                                }
                        else:
                            kwargs = {}

                        # Test based on dob and date_of_observation
                        dob = datetime.strptime(
                            get_field_2(row, "dob"),
                            "%m/%d/%Y",
                            )
                        date_of_observation = datetime.strptime(
                            get_field_2(row, "date_of_observation"),
                            "%m/%d/%Y",
                            )
                        obs_by_dates = Observation(
                            sex=sex,
                            dob=dob,
                            date_of_observation=date_of_observation,
                            )
                        method = getattr(obs_by_dates, method_name)
                        ours_by_dates = method(y, **kwargs)
                        self.assertAlmostEqual(
                            ours_by_dates, theirs, delta=DELTA
                            )

                        obs_by_age = Observation(
                            sex=sex,
                            age_in_months=age_in_months,
                            )
                        method = getattr(obs_by_age, method_name)
                        ours_by_age = method(y, **kwargs)
                        self.assertAlmostEqual(
                            ours_by_age, theirs, delta=DELTA
                            )

                        count += 1
        print(msg % count)

    def test_arm_circumference_for_age(self):
        self.perform_test_for_metric(
            y_name="arm_circumference",
            z_name="acfa_z",
            method_name="acfa",
            msg="Tested %s arm circumference values",
            )

    def test_bmi_for_age(self):
        self.perform_test_for_metric(
            y_name="bmi",
            z_name="bmifa_z",
            method_name="bmifa",
            msg="Tested %s BMI values",
            test_both_files=True,
            )

    def test_head_circumference_for_age(self):
        self.perform_test_for_metric(
            y_name="head_circumference",
            z_name="hcfa_z",
            method_name="hcfa",
            msg="Tested %s head circumference values",
            test_both_files=True,
            )

    def test_subscapular_skinfold_for_age(self):
        self.perform_test_for_metric(
            y_name="subscapular_skinfold",
            z_name="ssfa_z",
            method_name="ssfa",
            msg="Tested %s subscapular skinfold values",
            )

    def test_triceps_skinfold_for_age(self):
        self.perform_test_for_metric(
            y_name="triceps_skinfold",
            z_name="tsfa_z",
            method_name="tsfa",
            msg="Tested %s triceps skinfold values",
            )

    def test_weight_for_age(self):

        def filter2_(r):
            age_in_months = get_field_2(r, "age_in_months", as_d=True)
            return age_in_months and age_in_months < 119

        self.perform_test_for_metric(
            y_name="weight",
            z_name="wfa_z",
            method_name="wfa",
            filter2_=filter2_,
            msg="Tested %s weight values",
            test_both_files=True,
            )

    def test_length_for_age(self):
        self.perform_test_for_metric(
            y_name="height",
            z_name="lfa_z",
            method_name="lhfa",
            msg="Tested %s length-for-age values",
            method_kwargs={
                "recumbent": lambda r: get_field_1(r, "l_or_h") == "l"
                },
            method_kwargs2={
                "auto_adjust": lambda r: False,
                },
            test_both_files=True,
            )

    def test_weight_for_length(self):

        def filter_(row):
            return (
                get_field_1(row, "l_or_h") == "l" and
                get_field_1(row, "height", as_d=True) <= Decimal("110")
                )

        def filter2_(r):
            age_in_months = get_field_2(r, "age_in_months", as_d=True)
            return age_in_months and age_in_months < Decimal(24)

        self.perform_test_for_metric(
            y_name="weight",
            z_name="wfl_z",
            method_name="wfl",
            msg="Tested %s weight-for-length values",
            filter_=filter_,
            filter2_=filter2_,
            method_kwargs={"length": lambda r: get_field_1(r, "height")},
            method_kwargs2={"length": lambda r: get_field_2(r, "height")},
            test_both_files=True,
            )

    def test_weight_for_height(self):

        def filter2_(r):
            height = get_field_2(r, "height", as_d=True)
            age_in_months = get_field_2(r, "age_in_months", as_d=True)
            height_in_range = height and (65 < height < 120)
            age_in_range = age_in_months and Decimal(24) < age_in_months
            return height_in_range and age_in_range

        self.perform_test_for_metric(
            y_name="weight",
            z_name="wfl_z",
            method_name="wfh",
            msg="Tested %s weight-for-height values",
            filter_=lambda r: get_field_1(r, "l_or_h") == "h",
            filter2_=filter2_,
            method_kwargs={"height": lambda r: get_field_1(r, "height")},
            method_kwargs2={"height": lambda r: get_field_2(r, "height")},
            test_both_files=True,
            )

    def test_additional_data_for_arm_circumference_for_age(self):
        """A one-off that weakly just tests against round z-score values."""

        def test(sex):
            file_name = os.path.join(
                "pygrowup", "tables", "by_month", "src",
                "mramba_acfa_%(sex)s_5_19.txt" % {"sex": sex}
                )
            header2zscore = {
                "SD3neg": -3,
                "SD2neg": -2,
                "SD1neg": -1,
                "SD0": 0,
                "SD1": 1,
                "SD2": 2,
                "SD3": 3,
                }
            count = 0
            with open(file_name) as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    age_in_months = row["Month"]
                    # Tests are only month-level age granularity
                    obs_by_month = Observation(
                        sex=Observation.MALE if sex == "boys"
                        else Observation.FEMALE,
                        age_in_months=age_in_months,
                        )
                    for col, z_score in header2zscore.items():
                        y = row[col]
                        # These get reported back upon sub-test failure, to aid
                        # troubleshooting.
                        subtest_feedback = {
                            "sex": sex,
                            "age_in_months": age_in_months,
                            "measurement": y,
                            }
                        with self.subTest(**subtest_feedback):
                            ours_by_month = obs_by_month.acfa(
                                y, use_extra_data=True
                                )
                            self.assertAlmostEqual(
                                ours_by_month, z_score, delta=DELTA
                                )

                            count += 1
            return count
        tested = 0
        tested += test("boys")
        tested += test("girls")
        print("Tested %s additional arm circumference values" % tested)


class TestUnexpectedValues(unittest.TestCase):

    def test_sex_must_be_specified(self):
        with self.subTest(msg="Must supply sex"):
            with self.assertRaises(exceptions.ImproperlySpecifiedSex):
                Observation("")
        with self.subTest(msg="Sex must be properly specified"):
            with self.assertRaises(exceptions.ImproperlySpecifiedSex):
                Observation(sex="dude")

    def test_ages_must_be_properly_specified(self):
        with self.subTest(msg="Can't have negative ages"):
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                Observation(Observation.MALE, age_in_days=-1)
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                Observation(Observation.MALE, age_in_months=-1)
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                today = date.today()
                yesterday = today - timedelta(days=1)
                Observation(
                    Observation.MALE, dob=today, date_of_observation=yesterday,
                    )

        with self.subTest(msg="Age must be numeric"):
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                Observation(Observation.MALE, age_in_days="one")
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                Observation(Observation.MALE, age_in_months="two")

        with self.subTest(msg="Dates must be dates"):
            with self.assertRaises(exceptions.ImproperlySpecifiedAge):
                Observation(
                    Observation.MALE, dob="2017-08-21",
                    date_of_observation="2017-09-01",
                    )

    def test_acceptable_age_ranges(self):
        two_month_old = Observation(Observation.FEMALE, age_in_months=2.8)
        five_plus_year_old = Observation(Observation.FEMALE, age_in_months=62)
        ten_plus_year_old = Observation(
            Observation.MALE, age_in_months=10*12+1
            )
        nineteen_plus_year_old = Observation(
            Observation.MALE, age_in_months=19*12+1
            )

        with self.subTest(msg="Arm circumference age range: 3mos - 5 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                two_month_old.arm_circumference_for_age(20)
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                five_plus_year_old.arm_circumference_for_age(20)

        with self.subTest(msg="BMI age range: 0 - 19 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                nineteen_plus_year_old.bmi_for_age(20)

        with self.subTest(msg="Head circumference age range: 0 - 5 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                five_plus_year_old.head_circumference_for_age(20)

        with self.subTest(msg="Length/height-for-ge range: 0 - 19 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                nineteen_plus_year_old.length_or_height_for_age(20)

        with self.subTest(msg="Subscapular skinfold age range: 3mos - 5 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                two_month_old.subscapular_skinfold_for_age(20)
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                five_plus_year_old.subscapular_skinfold_for_age(20)

        with self.subTest(msg="Triceps skinfold age range: 3mos - 5 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                two_month_old.triceps_skinfold_for_age(20)
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                five_plus_year_old.triceps_skinfold_for_age(20)

        with self.subTest(msg="Weight-for-age range: 0 - 10 yrs"):
            with self.assertRaises(exceptions.AgeOutOfRangeError):
                ten_plus_year_old.triceps_skinfold_for_age(20)


if __name__ == '__main__':
    unittest.main()
