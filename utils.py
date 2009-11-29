#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from __future__ import with_statement

import os
import re
import datetime
import math
try:
    # NOTE Python 2.5 requires installation of simplejson library
    # http://pypi.python.org/pypi/simplejson
    import simplejson as json
except ImportError:
    # Python 2.6 includes json library
    import json

from tables import stunting_boys, stunting_girls
from tables import weight_for_height as weight_for_height_table

class childgrowth(object):
    def __init__(self):
        # load WHO Growth Standards
        # http://www.who.int/childgrowth/standards/en/

        WHO_tables = [
            'wfl_boys_0_2_zscores.json',  'wfl_girls_0_2_zscores.json',\
            'wfh_boys_2_5_zscores.json',  'wfh_girls_2_5_zscores.json',\
            'lhfa_boys_0_5_zscores.json', 'lhfa_girls_0_5_zscores.json',\
            'wfa_boys_0_5_zscores.json',  'wfa_girls_0_5_zscores.json']

        for table in WHO_tables:
            # TODO OS agnostic!
            table_file = 'apps/childhealth/tables/' + table
            with open(table_file, 'r') as f:
                # drop _zscores.json from table name and use
                # result as attribute name
                # (e.g., wfa_boys_0_5_zscores.json => wfa_boys_0_5)
                table_name, underscore, zscore_part =\
                    table.split('.')[0].rpartition('_')
                setattr(self, table_name, json.load(f))

    def _get_zscores_by_month(self, table_name, month):
        #print "getting scores by month: " + str(month)
        table = getattr(self, table_name)
        for scores in table:
            m = scores.get("Month")
            if m is not None:
                if int(m) == int(month):
                    #print scores
                    return scores
        print "SCORES NOT FOUND BY MONTH"

    def _get_zscores_by_height(self, table_name, height):
        #print "getting scores by height: " + str(height)
        table = getattr(self, table_name)
        # from the windoooows ... to the WALLS
        #lower_bound = math.floor(height)
        #upper_bound = math.ceil(height)
        # TODO interpolate?
        for scores in table:
            m = scores.get("Height")
            # not int or float here!
            # e.g., expecting 60 or 60.5
            if m == str(util._dumb_round(float(height))):
                #print scores
                return scores
        print "SCORES NOT FOUND BY HEIGHT"

    @staticmethod
    def _add_gender_to_string(table_name, gender):
        if gender == "M":
            table_name = table_name + 'boys_'
            return table_name
        elif gender == "F":
            table_name = table_name + 'girls_'
            return table_name
        else:
            raise 

    @staticmethod
    def _add_age_range_to_string(table_name, age_in_months):
        if age_in_months < 24:
            table_name = table_name + '0_2'
        if age_in_months  >= 24:
            table_name = table_name + '2_5'
        return table_name

    def test_zscores(self):
        import csv
        import codecs
        csvee = codecs.open("apps/childhealth/test.csv", "rU", encoding='utf-8', errors='ignore')

        # sniffer attempts to guess the file's dialect e.g., excel, etc
        #dialect = csv.Sniffer().sniff(csvee.read(1024))
        #csvee.seek(0)
        # DictReader uses first row of csv as key for data in corresponding column
        reader = csv.DictReader(csvee, dialect="excel")
        for row in reader:
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
                age = int(float(row["agemons"]))
                try:
                    our_result = self.zscore_for_measurement(indicator, measurement,\
                        age, gender, height)
                    print "-----------------------"
                    print indicator.upper() + " " + gender + " " + str(age)
                    print "THEM: " + str(their_result)
                    print "US  : " + str(our_result)
                except Exception, e:
                    print "-----------------------"
                    print indicator.upper() + " " + gender
                    print "OOPS: " + str(e)
                

        
    def zscore_for_measurement(self, indicator, measurement, age_in_months, gender, height=None):
        assert gender in ["M", "F"]
        assert indicator in ["lhfa", "wfl", "wfh", "wfa"] 
        debug = False

        # initial table string
        table_name = indicator + '_'
        # check gender and update table_name string
        table_name = self._add_gender_to_string(table_name, gender)

        # check age and update table_name string
        t = age_in_months
        if indicator in ["wfa", "lhfa"]:
            # weight for age has only one table per gender
            table_name = table_name + "0_5"
        else:
            # all other tables come as a pair: 0-2 and 2-5
            table_name = self._add_age_range_to_string(table_name, int(t))

        # get zscore from appropriate table
        if indicator == "wfh" and height is not None:
            zscores = self._get_zscores_by_height(table_name, height)
        else:
            zscores = self._get_zscores_by_month(table_name, t)

        if zscores is None:
            return None

        # this is our length or height or weight measurement
        y = float(measurement)
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
            if (float(65.7) < y < float(120.7)):
                if debug: print "subtracting 0.7 from length"
                if debug: print str(y)
                #y = y - float(0.7)
                if debug: print str(y)
        if indicator == "wfh":
            # add 0.7cm to all height measurements
            # (basically to convert all height measurments to lengths)
            if debug: print "adding 0.7 to height"
            if debug: print str(y)
            #y = y + float(0.7)
            if debug: print str(y)

        # fetch necessary scores from zscores dict and cast as floats
        # L(t)
        box_cox_power = float(zscores.get("L"))
        if debug: print "BOX-COX: " + str(box_cox_power)
        # M(t)
        median_for_age = float(zscores.get("M"))
        if debug: print "MEDIAN: " + str(median_for_age)
        # S(t)
        coefficient_of_variance_for_age = float(zscores.get("S"))
        if debug: print "COEF VAR: " + str(coefficient_of_variance_for_age)

        sd0 = float(zscores.get("SD0"))
        if debug: print "ST0: " + str(sd0)

        ###
        #           [y/M(t)]^L(t) - 1
        #   Zind =  -----------------
        #               S(t)L(t)
        ###

        zscore = ((((y / median_for_age)**box_cox_power) - float(1) ) /\
                        (coefficient_of_variance_for_age * box_cox_power))

        # somethings funky with the wfh and wfl z scores .. trying to debug
        zscore2 = ((((y / median_for_age)**box_cox_power) - float(1) ) /\
                        sd0)
        alt = (y - median_for_age) / (median_for_age *\
            coefficient_of_variance_for_age)
        #if indicator == "lhfa":
        #    zscore = alt
        if debug: print "Z: " + str(zscore)
        if debug: print "Z2: " + str(zscore2)
        if debug: print "Zalt: " + str(alt)
        #zscore =zscore2 

        if indicator not in ["wfl", "wfh", "wfa"]:
            # return length/height-for-age (lhfa) without further processing
            # L(t) is always 1 for this indicator, so differences between
            # adjacent SDs (e.g., 2 SD and 3 SD) are constant for a specific
            # age but varied at different ages
            return zscore
        elif (abs(zscore) <= float(3)):
            # (see below comment)
            return zscore
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
                stdev = median_for_age*(float(1) + box_cox_power *\
                    coefficient_of_variance_for_age * float(sd))**\
                    (float(1)/box_cox_power)
                return stdev
                
            if (zscore > float(3)):
                print "Z greater than 3"
                # TODO measure performance of lookup vs calculation
                # calculate for now so we have greater precision

                # get cutoffs from zscores dict
                #SD2pos = float(zscores.get("SD2"))
                #SD3pos = float(zscores.get("SD3"))

                # calculate SD
                SD2pos_c = calc_stdev(2)
                SD3pos_c = calc_stdev(3) 

                # compute distance
                #SD23pos = SD3pos - SD2pos
                SD23pos_c = SD3pos_c - SD2pos_c

                # compute final z-score
                zscore = float(3) + ((y - SD3pos_c)/SD23pos_c)
                return zscore

            if (zscore < float(-3)):
                print "Z less than 3"
                # get cutoffs from zscores dict
                #SD2neg = float(zscores.get("SD2neg"))
                #SD3neg = float(zscores.get("SD3neg"))

                # calculate SD
                SD2neg_c = calc_stdev(-2)
                SD3neg_c = calc_stdev(-3) 

                # compute distance
                #SD23neg = SD2neg - SD3neg
                SD23neg_c = SD2neg_c - SD3neg_c

                # compute final z-score
                zscore = float(-3) + ((y - SD3neg_c)/SD23neg_c)
                return zscore
        

class util(object):
    @staticmethod   
    def get_good_date(date):
        delimiters = r"[./\\-]+"
        # expecting YYYY-MM-DD, YY-MM-DD, or YY-M-D
        Allsect=re.split(delimiters,date)            
        if Allsect is not None:
            year = Allsect[0]
            day = Allsect[2]
            month = Allsect[1]         

            # make sure we have a REAL day
            if month.isdigit():
                if int(month) == 2:
                    if int(day) > 28:
                        day = 28
                if int(month) in [4, 6, 9, 11]:
                    if int(day) > 30:
                        day = 30
            else:
                return None

            # if there are letters in the date, give up
            if not year.isdigit():
                return None
            if not day.isdigit():
                return None

            # add leading digits if they are missing
            # TODO can we use datetime.strptime for this?
            if len(year) < 4 : 
                year = "20%s" % year        
            if len(month) < 2:
                month = "0%s" % month
            if len(day) < 2:
                day = "0%s" % day         

            # return ISO string for human consumption;
            # datetime.date for django consumption
            good_date_str = "%s-%s-%s" % (year,month,day )
            good_date_obj = datetime.date(int(year), int(month), int(day))
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
    def sloppy_date_to_age_in_months(date):
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
####
#
#  TODO the below functions are from andymckay's malnutrition work
#       and the SAM/MAM stuff in childhealth/models.py (on the
#       Assessment model) should be ported to use these functions
#       as well as the flat data files rather than having the
#       overhead of a HealthTables app 
#
####

    @staticmethod
    def years_months(date):
        now = datetime.now().date()
        ymonths = (now.year - date.year) * 12
        months = ymonths + (now.month - date.month)
        return (now.year - date.year, months)
        
    @staticmethod
    def stunting(date, gender):
        assert gender.lower() in ["m", "f"]
        years, months = years_months(date)
        # we have a month eg: 9, so we assume that is 8.5, since
        # it can't be 9.5... assuming the .5's are there to make sure that
        if int(months) > 73:
            raise ValueError, "Stunting charts only go as high as 72.5 months"
        elif int(months) >= 1:
            months = str(int(months) - 0.5)
        else:
            # lowest bound
            months = 0
            
        if gender.lower() == "m":
            stunts = stunting_boys.data
        else:
            stunts = stunting_girls.data
        return stunts[months]

    @staticmethod
    def _dumb_round(number):
        # please improve
        assert isinstance(number, (float, int)), "Got a %s, which is a: %s" % (number, type(number)) # forget duck typing, this won't work on anything else
        remainder = number - int(number)
        if remainder >= 0.5:
            remainder = 0.5
        else:
            remainder = 0.0
        return int(number) + remainder

    range_strs = ["60%-", "70%-60%","75%-70%", "80%-75%","85%-80%","100%-85%"]

    @staticmethod
    def _get_range_str(value, targets):
        targets.reverse()
        result = "60%-"
        for text, target in zip(range_strs, targets):
            target = float(target)
            if value >= target:
                result = text
        return result
        
    @staticmethod
    def weight_for_height(height, weight):
        weight = float(weight)
        number = _dumb_round(height)
        
        if number < 49.0:
            # raise ValueError, "Weight for height charts only go as low as 85.0, got height %s." % height
            return None
        elif number > 130.0:
            # raise ValueError, "Weight for height charts only go as high as 130.0, got height %s." % height
            return None
            
        targets = weight_for_height_data.data[str(number)][:]
        return _get_range_str(weight, targets)
