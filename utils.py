#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
import datetime
    
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
            if len(year) < 4 : 
                year = "20%s" % year        
            if len(month) < 2:
                month = "0%s" % month
            if len(day) < 2:
                day = "0%s" % day         
            good_date_string = "%s-%s-%s" % (year,month,day )
            good_date_obj = datetime.date(int(year), int(month), int(day))
            return good_date_string, good_date_obj

    @staticmethod
    def get_good_sex(gender):
        male_pattern = "(m[a-z]*)"
        female_pattern =  "(f[a-z]*)"
        its_a_boy = re.match(male_pattern, gender, re.I) 
        its_a_girl = re.match(female_pattern, gender, re.I) 
        if its_a_boy is not None:
            return 'M'
        elif its_a_girl is not None:
            return 'F'
        else:
            return None

    @staticmethod
    def sloppy_date_to_age_in_months(date):
        delta = datetime.date.today() - date
        years = delta.days / 365.25
        # FIXME: i18n
        return str(int(delta.days/30.4375))
