#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from __future__ import with_statement

import os
import re
import datetime
import math
import decimal
from decimal import Decimal as D

try:
    # NOTE Python 2.5 requires installation of simplejson library
    # http://pypi.python.org/pypi/simplejson
    import simplejson as json
except ImportError:
    # Python 2.6 includes json library
    import json

# TODO is this the best way to get this file's directory?
module_dir = os.path.split(os.path.abspath(__file__))[0]

class childgrowth(object):
    def __init__(self, adjust_height_data = False, adjust_weight_scores = False, american_standards = False):
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
        
        
        self.american_standards = american_standards

        # load WHO Growth Standards
        # http://www.who.int/childgrowth/standards/en/
        # WHO tab-separated txt files have been converted to json,
        # and the seperate lhfa tables (0-2 and 2-5) have been combined

        WHO_tables = [
            'wfl_boys_0_2_zscores.json',  'wfl_girls_0_2_zscores.json',\
            'wfh_boys_2_5_zscores.json',  'wfh_girls_2_5_zscores.json',\
            'lhfa_boys_0_5_zscores.json', 'lhfa_girls_0_5_zscores.json',\
            'hcfa_boys_0_5_zscores.json', 'hcfa_girls_0_5_zscores.json',\
            'wfa_boys_0_5_zscores.json',  'wfa_girls_0_5_zscores.json']

        # load CDC growth standards
        # http://www.cdc.gov/growthcharts/
        # CDC csv files have been converted to JSON, and the third standard
        # deviation has been fudged for the purpose of this tool.
        
        CDC_tables = [
            'lhfa_boys_2_20_zscores.cdc.json',     'lhfa_girls_2_20_zscores.cdc.json', \
            'wfa_boys_2_20_zscores.cdc.json',      'wfa_girls_2_20_zscores.cdc.json', \
            'bmifa_boys_2_20_zscores.cdc.json',    'bmifa_girls_2_20_zscores.cdc.json', ]

        # TODO is this the best way to find the tables?
        table_dir = os.path.join(module_dir, 'tables')
        for table in WHO_tables:
            table_file = os.path.join(table_dir, table)
            with open(table_file, 'r') as f:
                # drop _zscores.json from table name and use
                # result as attribute name
                # (e.g., wfa_boys_0_5_zscores.json => wfa_boys_0_5)
                table_name, underscore, zscore_part =\
                    table.split('.')[0].rpartition('_')
                setattr(self, table_name, json.load(f))
        if american_standards:
            for table in CDC_tables:
                    table_file = os.path.join(table_dir, table)
                    with open(table_file, 'r') as f:
                        # drop _zscores.cdc.json from table name and use
                        # result as attribute name
                        # (e.g., wfa_boys_0_5_zscores.json => wfa_boys_0_5)
                        table_name, underscore, zscore_part =\
                            table.split('.')[0].rpartition('_')
                        setattr(self, table_name, json.load(f))

    def _get_zscores_by_month(self, table_name, month):
        table = getattr(self, table_name)
        # TODO interpolate?
        closest_month = int(round(month))
        for scores in table:
            m = scores.get("Month")
            if m == str(closest_month):
                #print scores
                return scores
        print "SCORES NOT FOUND BY MONTH: " + str(month)

    def _get_zscores_by_height(self, table_name, height):
        table = getattr(self, table_name)
        # TODO be more clever?
        if table_name[2] == 'l':
            field_name = 'Length'
        elif table_name[2] == 'h':
            field_name = 'Height'
        else:
            print 'NOT L OR H????????????????'
        # find closest height from WHO table (which has data at a resolution
        # of half a centimeter). 
        # round height to closest tenth of a centimeter
        # NOTE months in table are not ints or floats
        # (e.g., 60, 60.5)
        # TODO interpolate?
        rounded_to_tenth = str(D(height).quantize(D('.1')))
        tenth = int(rounded_to_tenth[-1])
        # use the closest half centimeter
        if tenth in [0,1,2,8,9]:
            # remove decimal point too!
            closest_height = rounded_to_tenth[:-2]
        elif tenth in [3,4,6,7]:
            closest_height = rounded_to_tenth[:-1] + "5"
        else:
            # this should only be hit by heights ending in .5
            closest_height = rounded_to_tenth

        print "looking up scores with: " + closest_height
        for scores in table:
            h = scores.get(field_name)
            if h is not None:
                if h == closest_height:
                    #print scores
                    return scores
        print "SCORES NOT FOUND BY HEIGHT: " + str(height) + " -> " + closest_height

    @staticmethod
    def _add_gender_to_string(table_name, gender):
        if gender == "M":
            new_table_name = table_name + 'boys_'
            return new_table_name
        elif gender == "F":
            new_table_name = table_name + 'girls_'
            return new_table_name
        else:
            raise 

    @staticmethod
    def _add_age_range_to_string(table_name, age_in_months, american_standards):
        # CDC standards indicate that WHO standards should be used prior to 24 months
        if american_standards and age_in_months >= 24:
            new_table_name = table_name + "2_20"
            return new_table_name
        else:
            if int(age_in_months) < int(24):
                new_table_name = table_name + '0_2'
                return new_table_name
            elif int(age_in_months)  >= int(24):
                new_table_name = table_name + '2_5'
                return new_table_name
            else:
                raise

    def test_zscores(self):
        # TODO make this less embarassing..
        # TODO move this to a separate file
        import csv
        import codecs

        # test file is from WHO's igrowup software
        # please note that due to the increased precision and accuracy of this
        # implementation, some digits may be different because WHO's igrowup
        # software uses error-prone floating-point calculations
        test_file = os.path.join(module_dir, 'test.csv')
        csvee = codecs.open(test_file, "rU", encoding='utf-8', errors='ignore')

        # DictReader uses first row of csv as key for data in corresponding column
        reader = csv.DictReader(csvee, dialect="excel")
        self.diffs_one = []
        self.diffs_half = []
        self.errors = []
        rows = 0
        for row in reader:
            rows += 1
            for indicator in ["lhfa", "wfl", "wfh", "wfa"]:
                if row["GENDER"] == "1":
                    gender = "M"
                elif row["GENDER"] == "2":
                    gender = "F"
                else:
                    gender = None
                if indicator == "lhfa":
                    their_result = row["_ZLEN"]
                    measurement = row["HEIGHT"]
                    height = None
                if indicator in ["wfl", "wfh"]:
                    their_result = row["_ZWFL"]
                    measurement = row["WEIGHT"]
                    height = row["HEIGHT"]
                if indicator == "wfa":
                    their_result = row["_ZWEI"]
                    measurement = row["WEIGHT"]
                    height = None
                age = row["agemons"]

                try:
                    our_result = None
                    diff = None
                    print "-----------------------"
                    print indicator.upper() + " " + gender + " " + str(age) + " " + str(height)
                    our_result = self.zscore_for_measurement(indicator, measurement,\
                        age, gender, height)
                    print "THEM: " + str(their_result)
                    if our_result is not None:
                        print "US  : " + str(our_result)
                        diff = self.context.subtract(D(their_result), D(our_result))
                        #print " "
                        #print " "
                        if abs(diff) >= D(1):
                            self.diffs_one.append({'ind': indicator, 'gender': gender, 'age': age, 'us':our_result, 'them':their_result, 'diff':diff})
                            print "                                                          DIFF: " + str(diff) 
                        if abs(diff) >= D('0.5') and abs(diff) < D(1):
                            self.diffs_half.append({'ind': indicator, 'gender': gender, 'age': age, 'us':our_result, 'them':their_result, 'diff':diff})
                except AttributeError:
                    pass
                except Exception,e:
                    print "OOPS:                                                             " + str(e)
                    if their_result != "":
                        self.errors.append({'ind': indicator, 'gender': gender, 'age': age, 'us':our_result, 'them':their_result, 'diff':diff, 'e': e})

        print "__________________________________"
        print "TOTAL: " + str(rows)

        print "DIFFS OVER ONE: " + str(len(self.diffs_one))
        wfa = 0
        lhfa = 0
        wfl = 0
        wfh = 0
        wtf = 0
        for d in self.diffs_one:
            print d
            ind = d['ind']
            if ind == 'wfa':
                wfa += 1
            elif ind == 'lhfa':
                lhfa += 1
            elif ind == 'wfl':
                wfl += 1
            elif ind == 'wfh':
                wfh += 1
            else:
                wtf += 1
        print 'wfa: ' + str(wfa)
        print 'lhfa: ' + str(lhfa)
        print 'wfl: ' + str(wfl)
        print 'wfh: ' + str(wfh)
        print 'wtf: ' + str(wtf)

        print " "
        print "DIFFS OVER HALF: " + str(len(self.diffs_half))
        wfa = 0
        lhfa = 0
        wfl = 0
        wfh = 0
        wtf = 0
        for d in self.diffs_half:
            print d
            ind = d['ind']
            if ind == 'wfa':
                wfa += 1
            elif ind == 'lhfa':
                lhfa += 1
            elif ind == 'wfl':
                wfl += 1
            elif ind == 'wfh':
                wfh += 1
            else:
                wtf += 1
        print 'wfa: ' + str(wfa)
        print 'lhfa: ' + str(lhfa)
        print 'wfl: ' + str(wfl)
        print 'wfh: ' + str(wfh)
        print 'wtf: ' + str(wtf)

        print " "
        print "ERRORS: " + str(len(self.errors))
        wfa = 0
        lhfa = 0
        wfl = 0
        wfh = 0
        wtf = 0
        for d in self.errors:
            print d
            ind = d['ind']
            if ind == 'wfa':
                wfa += 1
            elif ind == 'lhfa':
                lhfa += 1
            elif ind == 'wfl':
                wfl += 1
            elif ind == 'wfh':
                wfh += 1
            else:
                wtf += 1
        print 'wfa: ' + str(wfa)
        print 'lhfa: ' + str(lhfa)
        print 'wfl: ' + str(wfl)
        print 'wfh: ' + str(wfh)
        print 'wtf: ' + str(wtf)
                

        
    def zscore_for_measurement(self, indicator, measurement, age_in_months, gender, height=None):
        assert gender.upper() in ["M", "F"]
        assert indicator.lower() in ["lhfa", "wfl", "wfh", "wfa", "bmifa", "hcfa"]
        debug = False
        # print indicator + " " + str(measurement) + " " + str(age_in_months)\
        #     + " " + str(gender)
        # print self.american_standards

        # initial table string
        table_name = indicator.lower() + '_'
        # check gender and update table_name string
        table_name = self._add_gender_to_string(table_name, gender)

        # check age and update table_name string
        t = D(age_in_months)
        if indicator.lower() in ["wfa", "lhfa"]:
            # weight for age has only one table per gender, and CDC goes unused before 24mos
            if self.american_standards and age_in_months >= 24:
                table_name = table_name + "2_20"
            else:
                table_name = table_name + "0_5"
        # head circumference for age is WHO-only and comes as a single 0-5
        elif indicator.lower() in ["hcfa"]:
            table_name = table_name + "0_5"
        # these two checks shouldnt be necessary, but just in case
        elif indicator.lower() in ["wfl"]:
            table_name = table_name + "0_2"
        elif indicator.lower() in ["wfh"]:
            table_name = table_name + "2_5"
        else:
            # all other tables come as a pair: 0-2 and 2-5 or 2-20
            table_name = self._add_age_range_to_string(table_name, t, self.american_standards)

        # this is our length or height or weight measurement
        y = D(measurement)
        if debug: print "MEASUREMENT: " + str(y)

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
        # print table_name
        if indicator.lower() in ["wfh", "wfl"]:
            if height is not None:
                zscores = self._get_zscores_by_height(table_name, height)
            else:
                print "NO LENGTH OR HEIGHT"
        if indicator.lower() in ["lhfa", "wfa", "bmifa", "hcfa"]:
            if t is not None:
                if self.american_standards:
                    # CDC standards are for ages 2-20
                    if t <= D(240):
                        # BMI for Age stats don't exist for 0-2
                        if indicator.lower() == 'bmifa' and t < D(24):
                            return 'TOO YOUNG'
                        # Head circumference for Age stats don't exist for 5-20
                        if indicator.lower() == "hcfa" and t > D(60):
                            return 'TOO OLD'
                        else:
                            zscores = self._get_zscores_by_month(table_name, t)
                    else:
                        return 'TOO OLD'                    
                else:
                    if t <= D(60):
                        zscores = self._get_zscores_by_month(table_name, t)
                    else:
                        return 'TOO OLD'
            else:
                print "NO AGE"

        if zscores is None:
            print "NO SCORES????????????????"
            return D('99.0')


        # fetch necessary scores from zscores dict and cast as decimals
        # L(t)
        box_cox_power = D(zscores.get("L"))
        if debug: print "BOX-COX: " + str(box_cox_power)
        # M(t)
        median_for_age = D(zscores.get("M"))
        if debug: print "MEDIAN: " + str(median_for_age)
        # S(t)
        coefficient_of_variance_for_age = D(zscores.get("S"))
        if debug: print "COEF VAR: " + str(coefficient_of_variance_for_age)
        
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
        power = math.pow(self.context.divide(y, median_for_age), box_cox_power)
        numerator  = D(str(power)) -  D(1)
        denomenator = self.context.multiply(coefficient_of_variance_for_age,\
                                                box_cox_power)
        zscore = self.context.divide(numerator, denomenator)


        # TODO this is probably unneccesary, as it should work out to be the
        # same as the above z-score calculation
        #if indicator == "lhfa":
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
                    ### e.g.,
                    #
                    #   SD3neg = M(t)[1 + L(t) * S(t) * (-3)]^ 1/L(t)
                    #   SD2pos = M(t)[1 + L(t) * S(t) * (2)]^ 1/L(t)
                    #
                    ###
                    base = self.context.add(D(1), self.context.multiply(\
                        self.context.multiply(box_cox_power,\
                        coefficient_of_variance_for_age), D(sd)))
                    exponent = self.context.divide(D(1), box_cox_power)
                    pow = math.pow(base, exponent)
                    stdev = self.context.multiply(median_for_age, D(str(pow)))
                    return D(stdev)
                    
                if (zscore > D(3)):
                    print "Z greater than 3"
                    # TODO measure performance of lookup vs calculation
                    # calculate for now so we have greater precision

                    # get cutoffs from z-scores dict
                    #SD2pos = D(zscores.get("SD2"))
                    #SD3pos = D(zscores.get("SD3"))

                    # calculate SD
                    SD2pos_c = calc_stdev(2)
                    SD3pos_c = calc_stdev(3)

                    # compute distance
                    SD23pos_c = SD3pos_c - SD2pos_c

                    # compute final z-score
                    #zscore = D(3) + ((y - SD3pos_c)/SD23pos_c)
                    sub = self.context.subtract(D(y), SD3pos_c)
                    div = self.context.divide(sub, SD23pos_c)
                    zscore = self.context.add(D(3), div)
                    return zscore.quantize(D('.01'))

                if (zscore < D(-3)):
                    # get cutoffs from z-scores dict
                    #SD2neg = D(zscores.get("SD2neg"))
                    #SD3neg = D(zscores.get("SD3neg"))

                    # calculate SD
                    SD2neg_c = calc_stdev(-2)
                    SD3neg_c = calc_stdev(-3)

                    # compute distance
                    SD23neg_c = SD2neg_c - SD3neg_c

                    # compute final z-score
                    #zscore = D(-3) + ((y - SD3neg_c)/SD23neg_c)
                    sub = self.context.subtract(D(y), SD3neg_c)
                    div = self.context.divide(sub, SD23neg_c)
                    zscore = self.context.add(D(-3), div)
                    return zscore.quantize(D('.01'))


class helpers(object):
    @staticmethod   
    def get_good_date(date, delimiter=False):
        # TODO parameter to choose formating
        # e.g., DDMMYY vs YYMMDD etc
        print 'getting good date...'
        print date
        delimiters = r"[./\\-]+"
        if delimiter:
            # expecting DDMMYY
            Allsect=re.split(delimiters,date)
        else:
            print 'no delimiter'
            if len(date) == 6:
                # assume DDMMYY
                Allsect = [date[:2], date[2:4], date[4:]]
            elif len(date) == 8:
                # assume DDMMYYYY
                Allsect = [date[:2], date[2:4], date[4:]]
            elif len(date) == 4:
                # assume DMYY
                Allsect = [date[0], date[1], date[2:]]
            elif len(date) == 5:
                # reject ambiguous dates
                return None, None
                #if int(date[:2]) > 31 and (0 < int(date[2]) >= 12):
                #    Allsect = [date[:2], date[2], date[2:]]
                #if int(date[0]) <= 12 and (0 < int(date[1:3]) <= 31): 
                #    Allsect = [date[0], date[1:3], date[2:]]
            else:
                return None, None

        if Allsect is not None:
            print Allsect
            year = Allsect[2]
            month = Allsect[1]
            day = Allsect[0]
            print 'year ' + str(year)
            print 'month ' + str(month)
            print 'day ' + str(day)

            # make sure we have a REAL day
            if month.isdigit():
                if int(month) == 2:
                    if int(day) > 28:
                        day = 28
                if int(month) in [4, 6, 9, 11]:
                    if int(day) > 30:
                        day = 30
            else:
                return None, None

            # if there are letters in the date, give up
            if not year.isdigit():
                return None, None
            if not day.isdigit():
                return None, None

            # add leading digits if they are missing
            # TODO can we use datetime.strptime for this?
            if len(year) < 4 :
                year = "20%s" % year
            if len(month) < 2:
                month = "0%s" % month
            if len(day) < 2:
                day = "0%s" % day

            print 'year ' + str(year)
            print 'month ' + str(month)
            print 'day ' + str(day)
            # return ISO string for human consumption;
            # datetime.date for django consumption
            good_date_str = "%s-%s-%s" % (year,month,day )
            print good_date_str
            good_date_obj = datetime.date(int(year), int(month), int(day))
            print good_date_obj
            return good_date_str, good_date_obj

    @staticmethod
    def get_good_sex(gender):
        # TODO improve patterns so 'monkey' isnt a match for 'male'
        male_pattern = "(m[a-z]*)"
        female_pattern =  "(f[a-z]*)"
        its_a_boy = re.match(male_pattern, gender, re.I)
        its_a_girl = re.match(female_pattern, gender, re.I)
        if its_a_boy is not None:
            return 'M'
        elif its_a_girl is not None:
            return 'F'
        else:
            # hermaphrodite? transgender?
            return None

    @staticmethod
    def date_to_age_in_months(date):
        delta = datetime.date.today() - date
        #years = delta.days / 365.25
        return str(int(delta.days/30.4375))

    @staticmethod
    def age_to_estimated_bday(age_in_months):
        try:
            if age_in_months.isdigit():
                years = int(age_in_months) / 12
                months = int(age_in_months) % 12
                est_year = abs(datetime.date.today().year - int(years))
                est_month = abs(datetime.date.today().month - int(months))
                if est_month == 0:
                    est_month = 1
                estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                return estimate
            else:
                return None
        except Exception, e:
            print e
