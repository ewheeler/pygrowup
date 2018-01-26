from decimal import Decimal, getcontext as get_decimal_context
from importlib import import_module

from . import exceptions

WEIGHT_BASED_INDICATORS = {
    "wfa",
    "wfl",
    "wfh",
    "bmifa",
    # Note: the WHO technical documentation doesn't discuss skinfold z-score
    # computation, but it appears that tests pass when the weight-based
    # adjustments are applied.
    "ssfa",
    "tsfa",
    }


class Observation(object):

    MALE = "male"
    FEMALE = "female"
    SEXES = (MALE, FEMALE)
    t = None  # age of child (in days) at observation

    def __init__(self, sex, age_in_days=None, age_in_months=None, dob=None,
                 date_of_observation=None):
        """Initialize an Observation.

        Args:
            sex: constant; one of MALE or FEMALE
            age_in_days: int
            age_in_months: int, float, or Decimal
            dob: child's date of birth. datetime.date instance
            date_of_observation: datetime.date instance

        Under most circumstances, an age must be supplied (or implied) by
        specifying age_in_months, age_in_days, or dob AND date_of_observation.
        (The exception to this is when the *only* z-score to be calculated is
        weight for length/height.)
        """
        if sex not in self.SEXES:
            raise exceptions.ImproperlySpecifiedSex(
                "Sex must be either '%s' or '%s'" % self.SEXES
                )
        self.sex = sex
        if age_in_days:
            try:
                self.t = int(age_in_days)
            except:
                raise exceptions.ImproperlySpecifiedAge(
                    "age_in_days must be numeric"
                    )
        elif age_in_months:
            try:
                age_in_months = Decimal(age_in_months)
            except:
                raise exceptions.ImproperlySpecifiedAge(
                    "age_in_months must be numeric"
                    )
            days_per_month = Decimal("365.25") / Decimal(12)
            # (Coercing Decimal => int is the same as taking its floor.)
            self.t = int(age_in_months * days_per_month)
        elif dob and date_of_observation:
            try:
                self.t = (date_of_observation - dob).days
            except:
                raise exceptions.ImproperlySpecifiedAge(
                    "dob and date_of_observation must be datetime.date or "
                    "datetime.datetime instances"
                    )
        if self.t < 0:
            raise exceptions.ImproperlySpecifiedAge(
                "date_of_observation must be later than dob"
                )

    def _get_box_cox_variables(self, table_name, sex, t):
        """Look up & return the l, m, s values for a given growth standard,
        sex, and t value.

        Args:
            table_name: one of our abbreviated names for the growth standards.
                (str)
            sex: either "male" or "female".
            y: the measurement in question (float or Decimal)
            t: age in days (int) or, for weight-for-length/height,
                length/height measurement in cm (Decimal)

        Returns:
            Dict with keys "l", "m", and "s".

        Raises:
            KeyError
        """
        # We have by-day data for all age-related metrics up to 5 years of age.
        # The two by-weight metrics' data are housed in the same place--their
        # t values will be Decimals.
        if t != self.t or t <= 1856:
            module_path = "pygrowup.tables.by_day.%s" % (table_name)
        else:
            # Must be an age-based metric for an age over 5 years. Round
            # age (in days) to nearest month.
            t = round(t / (365/12.))
            module_path = "pygrowup.tables.by_month.%s" % (table_name)
        try:
            source = import_module(module_path)
        except ImportError:
            # We're assuming that this age range has been vetted already, so
            # this isn't a case of, say, trying to get the head circumference
            # for a 10-year-old.
            raise exceptions.PyGrowUpException(
                "Unknown growth standard name (%s)" % table_name
                )
        table = source.DATA
        by_sex = table.get(sex)
        if not by_sex:
            raise exceptions.PyGrowUpException(
                "Can't find data by sex (%s)" % sex
                )
        result = by_sex.get(t)
        if not result:
            raise exceptions.ZScoreError(
                "t value out of range or not found (%s)" % t
                )
        return result

    def _get_first_pass_z_score(self, y, l, m, s):
        """Calculate and return a "first-pass" z-score given the key inputs
        derived from a child's age (or in some cases, length/height).

        ("First-pass" in this case refers to the fact that certain weight-based
        metrics require further refinement when -3 < z < 3.)

        The naming of the variables corresponds with the nomenclature in
        "WHO Child Growth Standards: Methods and development". See Chapter 7:
        "Computation of centiles and z-scores"
        http://www.who.int/entity/childgrowth/standards/technical_report/en/

        The age (or length/height for wfl/wfh) referenced above is called "t",
        and is not dealt with directly in this method, but it is referenced
        below in the args

        Args:
            y: the measurement in question (float or Decimal)
            l: aka L(t); Box-Cox power for t (Decimal)
            m: aka M(t); median for t (Decimal)
            s: aka S(t); coefficient of variation for t (Decimal)

        The returned value of this method is computed based on the formula
        found in that chapter. It will be a Decimal.
        """
        # Formula from Chapter 7:
        #
        #           [y/M(t)]^L(t) - 1
        #   Zind =  -----------------
        #               S(t)L(t)
        context = get_decimal_context()
        base = context.divide(y, m)
        power = base ** l
        numerator = power - Decimal(1)
        denominator = context.multiply(s, l)
        zscore = context.divide(numerator, denominator)
        return zscore.quantize(Decimal(".01"))

    def _adjust_weight_based_z_score(self, z_score, y, l, m, s):
        """Adjust first-pass z_score and return new value.

        To be used in cases where first-pass value is > 3 or < -3.

        See Chapter 7 of "Computation of centiles and z-scores" referenced
        above for the formulae.
        """
        context = get_decimal_context()
        exp = context.divide(Decimal(1), l)
        if z_score > Decimal("3"):
            # Formula:
            #             y - SD3pos
            # z*ind = 3 + ----------
            #              SD23pos
            # Where:
            # SD3pos = M(t)[1 + L(t)*S(t)*(3)]^1/L(t) and
            # SD23pos = M(t)[1 + L(t)*S(t)*(3)]^1/L(t) -
            #           M(t)[1 + L(t)*S(t)*(2)]^1/L(t)
            SD3pos_base = Decimal(1) + l * s * Decimal(3)
            SD3pos = m * SD3pos_base ** exp
            SD23pos_1 = Decimal(1) + l * s * Decimal(3)
            SD23pos_2 = Decimal(1) + l * s * Decimal(2)
            SD23pos = m * (SD23pos_1 ** exp) - m * (SD23pos_2 ** exp)
            z_score = Decimal(3) + context.divide((y - SD3pos), SD23pos)
        elif z_score < Decimal(-3):
            # Formula:
            #              y - SD3neg
            # z*ind = -3 + ----------
            #               SD23neg
            SD3neg_base = Decimal(1) + l * s * Decimal(-3)
            SD3neg = m * SD3neg_base ** exp
            SD23neg_1 = Decimal(1) + l * s * Decimal(-2)
            SD23neg_2 = Decimal(1) + l * s * Decimal(-3)
            SD23neg = m * (SD23neg_1 ** exp) - m * (SD23neg_2 ** exp)
            z_score = Decimal(-3) + context.divide((y - SD3neg), SD23neg)
        return z_score.quantize(Decimal(".01"))

    def _validate_t(self, t=None, lower=0, upper=None, msg=None):
        """Validate that the value t (self.t; in days, unless overridden) is
        within the range for a particular growth metric. Both boundaries are
        inclusive.

        Args:
            t: length or height value, when the metric is not "for-age". opt.
                float or Decimal
            lower: minimum number of days supported for a metric. int
            upper: maximum number of days supported for a metric. int
            msg: description of range. str

        Raises:
            MissingAgeError: if t is not supplied.
            AgeOutOfRangeError: if t is out of range
        Returns:
            None
        """
        if not msg:
            msg = "Range is %s to %s" % (lower, upper)
        t = t if t else self.t
        if t is None:
            msg = "No time data supplied. %s" % msg
            raise exceptions.MissingAgeError(msg)

        msg = '"t" value {t} outside of range. {range_descr}'.format(
            t=t, range_descr=msg
            )
        if t < lower:
            raise exceptions.AgeOutOfRangeError(msg)
        if upper and t > upper:
            raise exceptions.AgeOutOfRangeError(msg)

    def _validate_measurement(self, measurement, lower, upper, msg=None):
        """Validate that the measurement value is within the range for a
        particular growth metric. Both boundaries are inclusive. The range
        should be very, very generous!

        Args:
            y: The measurement in question. int, float, Decimal
            lower: minimum number of days supported for a metric. int
            upper: maximum number of days supported for a metric. int
            msg: description of range. str

        Raises:
            MeasurementOutOfRangeError if measurement is outside the range.
            ImproperlySpecifiedMeasurement if measurement is not numeric.
        Returns:
            measurement value as Decimal
        """
        if not msg:
            msg = "Range is %s to %s" % (lower, upper)
        if not measurement:  # 0 isn't legitimate!
            msg = "No measurement supplied. %s" % msg
            raise exceptions.ImproperlySpecifiedMeasurement(msg)

        try:
            y = Decimal(measurement)
        except:
            raise exceptions.ImproperlySpecifiedMeasurement(
                "Measurement must be numeric."
                )

        msg = "Measurement value {y} outside of range. {range_descr}".format(
            y=measurement, range_descr=msg
            )
        if y < lower:
            raise exceptions.MeasurementOutOfRangeError(msg)
        if upper and y > upper:
            raise exceptions.MeasurementOutOfRangeError(msg)
        return y

    def get_z_score(self, table_name, sex, y, t):
        """Calculate and return a z-score.

        Args:
            table_name: one of our abbreviated names for the growth standards.
                (str)
            sex: either "male" or "female".
            y: the measurement in question (float or Decimal)
            t: age in days (int) or, for weight-for-length/height,
                length/height measurement in cm (Decimal)

        Returns:
            Decimal
        Raises:
            ValueError for exceptional values of y or t.
        """
        lms = self._get_box_cox_variables(table_name, sex, t)
        z_score = self._get_first_pass_z_score(y, **lms)
        if table_name in WEIGHT_BASED_INDICATORS and abs(z_score) > Decimal(3):
            z_score = self._adjust_weight_based_z_score(z_score, y, **lms)
        return z_score

    def acfa(self, measurement, use_extra_data=False):
        """Return the arm circumference-for-age z-score (aka MUAC).

        When using WHO data, the valid age range is 3 months to 5 years. If
        use_extra_data is set to True, the Mramba, et al, data set is available
        for children between 5 and 19 years. See README for details on this.

        Args:
            measurement: mid-upper arm circumference measurement (in cm).
                float or Decimal
            use_extra_data: allow the usage of an additional data set to serve
                children 5-19. Bool.
        """
        if use_extra_data:
            self._validate_t(
                lower=91, upper=19*365.25,
                msg="Range is 3 months to 19 years when use_extra_data is "
                "True."
                )
        else:
            self._validate_t(
                lower=91, upper=1856,
                msg="Range is 3 months to 5 years. Pass use_extra_data=True "
                "for children 5-19."
                )
        upper_bound = 60 if use_extra_data else 40
        y = self._validate_measurement(measurement, 3, upper_bound)
        return self.get_z_score(
            table_name="acfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def bmifa(self, measurement):
        """Return the BMI (body mass index)-for-age z-score.

        Args:
            measurement: BMI value. float or Decimal
        """
        self._validate_t(
            lower=0, upper=19*365, msg="Range is birth to 19 years."
            )
        y = self._validate_measurement(measurement, 5, 60)
        return self.get_z_score(
            table_name="bmifa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def hcfa(self, measurement):
        """Return the head circumference-for-age z-score.

        Args:
            measurement: head circumference measurement (in cm).
                float or Decimal
        """
        self._validate_t(
            lower=0, upper=1856, msg="Range is birth to 5 years."
            )
        y = self._validate_measurement(measurement, 10, 150)
        return self.get_z_score(
            table_name="hcfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def lhfa(self, measurement, recumbent=False, auto_adjust=True):
        """Return the length/height-for-age z-score.

        Args:
            measurement: length measurement (in cm) as float or Decimal
            recumbent: was the measurement taken with child lying down? Ignored
                for children under 2 years, or if auto_adjust is False. Bool.
            auto_adjust: if child is over 2 years and measured recumbently,
                adjust the measurement to convert to a (simulated) height.
                Bool.
        """
        self._validate_t(
            lower=0, upper=19*365, msg="Range is birth to 19 years."
            )
        y = self._validate_measurement(measurement, 10, 200)
        if self.t >= 365 * 2 and auto_adjust and recumbent:
            y -= Decimal("0.7")
        return self.get_z_score(
            table_name="lfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def ssfa(self, measurement):
        """Return the subscapular skinfold-for-age z-score.

        Args:
            measurement: measurement (in mm) as float or Decimal
        """
        self._validate_t(
            lower=91, upper=1856, msg="Range is 3 months to 5 years."
            )
        y = self._validate_measurement(measurement, 1, 30)
        return self.get_z_score(
            table_name="ssfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def tsfa(self, measurement):
        """Return the triceps skinfold-for-age z-score.

        Args:
            measurement: measurement (in mm) as float or Decimal
        """
        self._validate_t(
            lower=91, upper=1856, msg="Range is 3 months to 5 years."
            )
        y = self._validate_measurement(measurement, 1, 30)
        return self.get_z_score(
            table_name="tsfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def wfa(self, measurement):
        """Return the weight-for-age z-score.

        Args:
            measurement: weight measurement (in kg) as float or Decimal
        """
        self._validate_t(
            lower=0, upper=10*365, msg="Range is birth to 10 years."
            )
        y = self._validate_measurement(measurement, 1, 125)
        return self.get_z_score(
            table_name="wfa",
            y=y,
            sex=self.sex,
            t=self.t,
            )

    def wfh(self, weight, height):
        """Return the weight-for-height z-score for the supplied inputs.

        Args:
            weight: weight measurement (in kg) as float or Decimal
            height: height measurement (in cm) as float or Decimal
        """
        t = Decimal(height).quantize(Decimal("1.0"))
        self._validate_t(
            t=t, lower=65, upper=120,
            msg="Height range is 65cm to 120 cm."
            )
        y = self._validate_measurement(weight, 1, 125)
        return self.get_z_score(
            table_name="wfh",
            y=y,
            sex=self.sex,
            t=t,
            )

    def wfl(self, weight, length):
        """Return the weight-for-length z-score for the supplied inputs.

        Args:
            weight: weight measurement (in kg) as float or Decimal
            length: length measurement (in cm) as float or Decimal
        """
        t = Decimal(length).quantize(Decimal("1.0"))
        self._validate_t(
            t=t, lower=45, upper=110,
            msg="Length range is 45cm to 110 cm.",
            )
        y = self._validate_measurement(weight, 1, 125)
        return self.get_z_score(
            table_name="wfl",
            y=y,
            sex=self.sex,
            t=t,
            )

    # More verbose aliases for our metrics methods, in case you're into that.
    arm_circumference_for_age = acfa
    bmi_for_age = bmifa
    head_circumference_for_age = hcfa
    length_or_height_for_age = lhfa
    subscapular_skinfold_for_age = ssfa
    triceps_skinfold_for_age = tsfa
    weight_for_age = wfa
    weight_for_height = wfh
    weight_for_length = wfl
