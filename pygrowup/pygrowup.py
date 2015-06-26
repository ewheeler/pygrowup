#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import os
import math
import decimal
import logging
import json
from decimal import Decimal as D

import six

from . import exceptions


# TODO is this the best way to get this file's directory?
module_dir = os.path.split(os.path.abspath(__file__))[0]


class Observation(object):
    def __init__(self, indicator, measurement, age_in_months, sex,
                 height, american, logger_name):
        self.logger = logging.getLogger(logger_name)

        self.indicator = indicator
        self.measurement = measurement
        self.position = None
        self.age = D(age_in_months)
        self.sex = sex.upper()
        self.height = height
        self.american = american

        self.table_indicator = None
        self.table_age = None
        self.table_sex = None
        if self.indicator in ['wfl', 'wfh']:
            if self.height in ['', ' ', None]:
                raise exceptions.InvalidMeasurement('no length or height')

    @property
    def age_in_weeks(self):
        return ((self.age * D('30.4374')) / D(7))

    @property
    def rounded_height(self):
        """ Rounds height to closest half centimeter -- the resolution
            of the WHO tables. Oddly, the WHO tables do not include
            decimal places for whole centimeters, so some strange
            rounding is necessary (e.g., 89 not 89.0).
        """
        # round height to closest half centimeter
        correction = D('0.5') if D(self.height) >= D(0) else D('-0.5')
        rounded = int(D(self.height) / D('0.5') + correction) * D('0.5')
        # if closest half centimeter is an integer,
        # return as integer without decimal
        if rounded.as_tuple().digits[-1] == 0:
            return D(int(rounded)).to_eng_string()
        # otherwise return with decimal places
        return rounded.to_eng_string()

    def get_zscores(self, growth):
        table_name = self.resolve_table()
        table = getattr(growth, table_name)
        if self.indicator in ["wfh", "wfl"]:
            assert self.height is not None
            if D(self.height) < D(45):
                raise exceptions.InvalidMeasurement("too short")
            if D(self.height) > D(120):
                raise exceptions.InvalidMeasurement("too tall")
            # find closest height from WHO table (which has data at a resolution
            # of half a centimeter).
            # round height to closest tenth of a centimeter
            # NOTE heights in tables are EITHER ints or floats!
            # (e.g., 60, 60.5)
            closest_height = self.rounded_height
            self.logger.debug("looking up scores with: %s" % closest_height)
            scores = table.get(closest_height)
            if scores is not None:
                return scores
            raise exceptions.DataNotFound("SCORES NOT FOUND BY HEIGHT: %s => "
                                          "%s" % (self.height, closest_height))

        elif self.indicator in ["lhfa", "wfa", "bmifa", "hcfa"]:
            if self.age_in_weeks <= D(13):
                closest_week = str(int(math.floor(self.age_in_weeks)))
                scores = table.get(closest_week)
                if scores is not None:
                    return scores
                raise exceptions.DataNotFound("SCORES NOT FOUND BY WEEK: %s => "
                                              " %s" % (str(self.age_in_weeks),
                                                       closest_week))
            closest_month = str(int(math.floor(self.age)))
            scores = table.get(closest_month)
            if scores is not None:
                return scores
            raise exceptions.DataNotFound("SCORES NOT FOUND BY MONTH: %s =>"
                                          " %s" % (str(self.age),
                                                   closest_month))

    def resolve_table(self):
        """ Choose a WHO/CDC table to use, making adjustments
        based on age, length, or height. If, for example, the
        indicator is set to wfl while the child is too long for
        the recumbent tables, this method will make the lookup
        in the wfh table. """
        if self.indicator == 'wfl' and D(self.height) > D(86):
            self.logger.warning('too long for recumbent')
            self.table_indicator = 'wfh'
            self.table_age = '2_5'
        elif self.indicator == 'wfh' and D(self.height) < D(65):
            self.logger.warning('too short for standing')
            self.table_indicator = 'wfl'
            self.table_age = '0_2'
        else:
            self.table_indicator = self.indicator
            if self.table_indicator == 'wfl':
                self.table_age = '0_2'
            if self.table_indicator == 'wfh':
                self.table_age = '2_5'

        if self.sex == 'M':
            self.table_sex = 'boys'
        if self.sex == 'F':
            self.table_sex = 'girls'

        # weight for age has only one table per sex,
        # as does head circumference for age
        # and CDC goes unused before 24mos
        if self.indicator in ["wfa", "lhfa", "hcfa"]:
            self.table_age = "0_5"
            if self.age <= D(3):
                if self.age_in_weeks <= D(13):
                    self.table_age = "0_13"
            if self.american and self.age >= D(24):
                if self.indicator == "hcfa":
                    raise exceptions.InvalidAge('TOO OLD: %d' % self.age)
                self.table_age = "2_20"
        elif self.indicator in ["bmifa"]:
            if self.age > D(240):
                raise exceptions.InvalidAge('TOO OLD: %d' % self.age)
            elif self.age <= D(3) and self.age_in_weeks <= D(13):
                self.table_age = "0_13"
            elif self.age < D(24):
                self.table_age = '0_2'
            elif self.age >= D(24) and self.age <= D(60):
                self.table_age = '2_5'
            elif self.age >= D(24) and self.age > D(60):
                self.table_age = '2_20'
            else:
                raise exceptions.DataNotFound()
        else:
            if self.table_age is None:
                if self.table_indicator == 'wfl':
                    self.table_age = '0_2'
                if self.table_indicator == 'wfh':
                    self.table_age = '2_5'
                if self.age < D(24):
                    if self.table_indicator == 'wfh':
                        self.logger.warning('too young for standing')
                        self.table_indicator == 'wfl'
                    self.table_age = '0_2'
                elif self.age >= D(24):
                    if self.table_indicator == 'wfl':
                        self.logger.warning('too old for recumbent')
                        self.table_indicator == 'wfh'
                    self.table_age = '2_5'
                else:
                    raise exceptions.DataNotFound()
        table = "%(table_indicator)s_%(table_sex)s_%(table_age)s" %\
                {"table_indicator": self.table_indicator,
                 "table_sex": self.table_sex,
                 "table_age": self.table_age}
        self.logger.debug(table)
        # raise if any table name parts have not been resolved
        if not all([self.table_indicator, self.table_sex, self.table_age]):
            raise exceptions.DataError()
        return table


class Calculator(object):

    def __reformat_table(self, table_name):
        """ Reformat list of dicts to single dict
        with each item keyed by age, length, or height."""
        list_of_dicts = getattr(self, table_name)
        if 'Length' in list_of_dicts[0]:
            field_name = 'Length'
        elif 'Height' in list_of_dicts[0]:
            field_name = 'Height'
        elif 'Month' in list_of_dicts[0]:
            field_name = 'Month'
        elif 'Week' in list_of_dicts[0]:
            field_name = 'Week'
        else:
            raise exceptions.DataError('error loading: %s' % table_name)
        new_dict = {'field_name': field_name}
        for d in list_of_dicts:
            new_dict.update({d[field_name]: d})
        setattr(self, table_name, new_dict)

    def __init__(self, adjust_height_data=False, adjust_weight_scores=False,
                 include_cdc=False, logger_name='pygrowup', log_level="INFO"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level))

        # use decimal.Decimal instead of float to avoid unwanted rounding
        # http://docs.sun.com/source/806-3568/ncg_goldberg.html
        # TODO set a custom precision
        self.context = decimal.getcontext()

        # Height adjustments are part of the WHO specification
        # (to correct for recumbent vs standing measurements),
        # but none of the existing software seems to implement this.
        # default is false so values are closer to those produced
        # by igrowup software
        self.adjust_height_data = adjust_height_data

        # WHO specs include adjustments to z-scores of weight-based
        # indicators that are greater than +/- 3 SDs. These adjustments
        # correct for right skewness and avoid making assumptions about
        # the distribution of data beyond the limits of the observed values.
        # However, when calculating z-scores in a live data collection
        # situation, z-scores greater than +/- 3 SDs are likely to indicate
        # data entry or anthropometric measurement errors and should not
        # be adjusted. Instead, these large z-scores should be used to
        # identify poor data quality and/or entry errors.
        # These z-score adjustments are appropriate only when there
        # is confidence in data quality.
        self.adjust_weight_scores = adjust_weight_scores

        self.include_cdc = include_cdc

        # load WHO Growth Standards
        # http://www.who.int/childgrowth/standards/en/
        # WHO tab-separated txt files have been converted to json,
        # and the seperate lhfa tables (0-2 and 2-5) have been combined

        WHO_tables = [
            'wfl_boys_0_2_zscores.json',  'wfl_girls_0_2_zscores.json',
            'wfh_boys_2_5_zscores.json',  'wfh_girls_2_5_zscores.json',
            'lhfa_boys_0_5_zscores.json', 'lhfa_girls_0_5_zscores.json',
            'hcfa_boys_0_5_zscores.json', 'hcfa_girls_0_5_zscores.json',
            'wfa_boys_0_5_zscores.json',  'wfa_girls_0_5_zscores.json',
            'wfa_boys_0_13_zscores.json',  'wfa_girls_0_13_zscores.json',
            'lhfa_boys_0_13_zscores.json', 'lhfa_girls_0_13_zscores.json',
            'hcfa_boys_0_13_zscores.json', 'hcfa_girls_0_13_zscores.json',
            'bmifa_boys_0_13_zscores.json', 'bmifa_girls_0_13_zscores.json',
            'bmifa_boys_0_2_zscores.json',  'bmifa_girls_0_2_zscores.json',
            'bmifa_boys_2_5_zscores.json',  'bmifa_girls_2_5_zscores.json']

        # load CDC growth standards
        # http://www.cdc.gov/growthcharts/
        # CDC csv files have been converted to JSON, and the third standard
        # deviation has been fudged for the purpose of this tool.

        CDC_tables = [
            'lhfa_boys_2_20_zscores.cdc.json',
            'lhfa_girls_2_20_zscores.cdc.json',
            'wfa_boys_2_20_zscores.cdc.json',
            'wfa_girls_2_20_zscores.cdc.json',
            'bmifa_boys_2_20_zscores.cdc.json',
            'bmifa_girls_2_20_zscores.cdc.json', ]

        # TODO is this the best way to find the tables?
        table_dir = os.path.join(module_dir, 'tables')
        tables_to_load = WHO_tables
        if self.include_cdc:
            tables_to_load = tables_to_load + CDC_tables
        for table in tables_to_load:
            table_file = os.path.join(table_dir, table)
            with open(table_file, 'r') as f:
                # drop _zscores.json from table name and use
                # result as attribute name
                # (e.g., wfa_boys_0_5_zscores.json => wfa_boys_0_5)
                table_name, underscore, zscore_part =\
                    table.split('.')[0].rpartition('_')
                setattr(self, table_name, json.load(f))
                self.__reformat_table(table_name)

    # convenience methods
    def lhfa(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate length/height-for-age """
        return self.zscore_for_measurement('lhfa', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def wfl(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate weight-for-length """
        return self.zscore_for_measurement('wfl', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def wfh(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate weight-for-height """
        return self.zscore_for_measurement('wfh', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def wfa(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate weight-for-age """
        return self.zscore_for_measurement('wfa', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def bmifa(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate body-mass-index-for-age """
        return self.zscore_for_measurement('bmifa', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def hcfa(self, measurement=None, age_in_months=None, sex=None, height=None):
        """ Calculate head-circumference-for-age """
        return self.zscore_for_measurement('hcfa', measurement=measurement,
                                           age_in_months=age_in_months,
                                           sex=sex, height=height)

    def zscore_for_measurement(self, indicator, measurement, age_in_months, sex, height=None):
        assert sex is not None
        assert isinstance(sex, six.string_types)
        assert sex.upper() in ["M", "F"]
        assert age_in_months is not None
        assert indicator is not None
        assert indicator.lower() in ["lhfa", "wfl", "wfh", "wfa", "bmifa", "hcfa"]
        # reject blank measurements
        assert measurement not in ['', ' ', None]

        # this is our length or height or weight or bmi measurement.
        # allow exception if measurement cannot be cast as Decimal
        y = D(measurement)
        if y <= D(0):
            # reject measurements 0 or less because the math won't work.
            # and that would be an impossibly shaped human.
            raise exceptions.InvalidMeasurement('measurement must be greater'
                                                ' than zero')
        self.logger.debug("MEASUREMENT: %d" % y)

        obs = Observation(indicator, measurement, age_in_months, sex, height,
                          self.include_cdc, self.logger.name)

        # indicator-specific methodology
        # (see section 5.1 of http://www.who.int/entity/childgrowth/standards/\
        #                                  technical_report/en/index.html)
        #
        # TODO accept a recumbent vs standing parameter for deciding
        # whether or not to do these adjustments rather than assuming
        # measurement orientation based on the measurement
        if indicator == "wfl":
            # subtract 0.7cm from length measurements in this range
            # to adjust for child's reclined position
            if (D('65.7') < y < D('120.7')):
                y = y - D('0.7')

        if indicator == "wfh" and self.adjust_height_data:
            # add 0.7cm to all height measurements
            # (basically to convert all height measurments to lengths)
            y = y + D('0.7')

        # get zscore from appropriate table
        zscores = obs.get_zscores(self)

        if zscores is None:
            raise exceptions.DataNotFound()

        # fetch necessary scores from zscores dict and cast as decimals
        # L(t)
        box_cox_power = D(zscores.get("L"))
        self.logger.debug("BOX-COX: %d" % box_cox_power)
        # M(t)
        median_for_age = D(zscores.get("M"))
        self.logger.debug("MEDIAN: %d" % median_for_age)
        # S(t)
        coefficient_of_variance_for_age = D(zscores.get("S"))
        self.logger.debug("COEF VAR: %d" % coefficient_of_variance_for_age)

        ###
        # calculate z-score
        #
        # (see Chapter 7 of http://www.who.int/entity/childgrowth/standards/\
        #                                  technical_report/en/index.html)
        #
        #           [y/M(t)]^L(t) - 1
        #   Zind =  -----------------
        #               S(t)L(t)
        ###
        base = self.context.divide(y, median_for_age)
        self.logger.debug("BASE: %d" % base)
        power = base ** box_cox_power
        self.logger.debug("POWER: %d" % power)
        numerator = D(str(power)) - D(1)
        self.logger.debug("NUMERATOR: %d" % numerator)
        denomenator = self.context.multiply(coefficient_of_variance_for_age,
                                            box_cox_power)
        self.logger.debug("DENOMENATOR: %d" % denomenator)
        zscore = self.context.divide(numerator, denomenator)
        self.logger.debug("ZSCORE: %d" % zscore)

        # TODO this is probably unneccesary, as it should work out to be the
        # same as the above z-score calculation
        # if indicator == "lhfa":
        #    numerator_lhfa = self.context.subtract(D(y), median_for_age)
        #    denomenator_lhfa = self.context.multiply(median_for_age,\
        #        coefficient_of_variance_for_age)
        #    zscore_lhfa = self.context.divide(numerator_lhfa, denomenator_lhfa)
        #    zscore = zscore_lhfa

        # return z-score unless adjust_weight_scores indicates that
        # further processing is desired (see comment in __init__())
        if not self.adjust_weight_scores:
            # round to hundreth and return
            return zscore.quantize(D('.01'))
        else:
            if indicator not in ["wfl", "wfh", "wfa"]:
                # return length/height-for-age (lhfa) without further processing
                # L(t) is always 1 for this indicator, so differences between
                # adjacent SDs (e.g., 2 SD and 3 SD) are constant for a specific
                # age but varied at different ages
                return zscore.quantize(D('.01'))
            elif (abs(zscore) <= D(3)):
                # (see below comment)
                return zscore.quantize(D('.01'))
            else:
                # weight-based indicators present right-skewed distributions
                # so use restricted application of LMS method (limiting Box-Cox
                # normal distribution to interval corresponding to z-scores where
                # empirical data are available. z-scores beyond +/- 3 SDs are
                # fixed to the distance between +/- 2 SDs and +/- 3 SD
                # this avoids making assumptions about the distribution of data
                # beyond the limits of observed values
                #
                #            _
                #           |
                #           |       Zind            if |Zind| <= 3
                #           |
                #           |
                #           |       y - SD3pos
                #   Zind* = | 3 + ( ----------- )   if Zind > 3
                #           |         SD23pos
                #           |
                #           |
                #           |
                #           |        y - SD3neg
                #           | -3 + ( ----------- )  if Zind < -3
                #           |          SD23neg
                #           |
                #           |_
                def calc_stdev(sd):
                    #   e.g.,
                    #
                    #   SD3neg = M(t)[1 + L(t) * S(t) * (-3)]^ 1/L(t)
                    #   SD2pos = M(t)[1 + L(t) * S(t) * (2)]^ 1/L(t)
                    #
                    ###
                    base = self.context.add(D(1), self.context.multiply(
                        self.context.multiply(box_cox_power,
                                              coefficient_of_variance_for_age), D(sd)))
                    exponent = self.context.divide(D(1), box_cox_power)
                    power = math.pow(base, exponent)
                    stdev = self.context.multiply(median_for_age, D(str(power)))
                    return D(stdev)

                if (zscore > D(3)):
                    logging.info("Z greater than 3")
                    # TODO measure performance of lookup vs calculation
                    # calculate for now so we have greater precision

                    # get cutoffs from z-scores dict
                    # SD2pos = D(zscores.get("SD2"))
                    # SD3pos = D(zscores.get("SD3"))

                    # calculate SD
                    SD2pos_c = calc_stdev(2)
                    SD3pos_c = calc_stdev(3)

                    # compute distance
                    SD23pos_c = SD3pos_c - SD2pos_c

                    # compute final z-score
                    # zscore = D(3) + ((y - SD3pos_c)/SD23pos_c)
                    sub = self.context.subtract(D(y), SD3pos_c)
                    div = self.context.divide(sub, SD23pos_c)
                    zscore = self.context.add(D(3), div)
                    return zscore.quantize(D('.01'))

                if (zscore < D(-3)):
                    # get cutoffs from z-scores dict
                    # SD2neg = D(zscores.get("SD2neg"))
                    # SD3neg = D(zscores.get("SD3neg"))

                    # calculate SD
                    SD2neg_c = calc_stdev(-2)
                    SD3neg_c = calc_stdev(-3)

                    # compute distance
                    SD23neg_c = SD2neg_c - SD3neg_c

                    # compute final z-score
                    # zscore = D(-3) + ((y - SD3neg_c)/SD23neg_c)
                    sub = self.context.subtract(D(y), SD3neg_c)
                    div = self.context.divide(sub, SD23neg_c)
                    zscore = self.context.add(D(-3), div)
                    return zscore.quantize(D('.01'))
