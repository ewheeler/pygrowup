#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from __future__ import with_statement

import os
import re
import datetime
try:
    # NOTE Python 2.5 requires installation of simplejson library
    # http://pypi.python.org/pypi/simplejson
    import simplejson as json
except ImportError:
    # Python 2.6 includes json library
    import json

from tables import stunting_boys, stunting_girls
from tables import weight_for_height as weight_for_height_table

class util(object):
    def __init__(self):
        # load WHO Growth Standards
        # http://www.who.int/childgrowth/standards/en/

        WHO_tables = [
            'wfl_boys_0_2_zscores.json',  'wfl_girls_0_2_zscores.json',\
            'wfh_boys_2_5_zscores.json',  'wfh_girls_2_5_zscores.json',\
            'lhfa_boys_0_2_zscores.json', 'lhfa_girls_0_2_zscores.json',\
            'lhfa_boys_2_5_zscores.json', 'lhfa_girls_2_5_zscores.json',\
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
