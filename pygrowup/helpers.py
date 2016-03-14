import re
import datetime
import logging


def get_good_date(date, delimiter=False):
    # TODO parameter to choose formating
    # e.g., DDMMYY vs YYMMDD etc
    logging.debug('getting good date...')
    logging.debug(date)
    delimiters = r"[./\\-]+"
    if delimiter:
        # expecting DDMMYY
        Allsect = re.split(delimiters, date)
    else:
        logging.debug('no delimiter')
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
        logging.debug(Allsect)
        year = Allsect[2]
        month = Allsect[1]
        day = Allsect[0]
        logging.debug('year ' + str(year))
        logging.debug('month ' + str(month))
        logging.debug('day ' + str(day))

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
        if len(year) < 4:
            year = "20%s" % year
        if len(month) < 2:
            month = "0%s" % month
        if len(day) < 2:
            day = "0%s" % day

        logging.debug('year ' + str(year))
        logging.debug('month ' + str(month))
        logging.debug('day ' + str(day))
        # return ISO string for human consumption;
        # datetime.date for django consumption
        good_date_str = "%s-%s-%s" % (year, month, day)
        logging.debug(good_date_str)
        good_date_obj = datetime.date(int(year), int(month), int(day))
        logging.debug(good_date_obj)
        return good_date_str, good_date_obj


def get_good_sex(gender):
    # TODO improve patterns so 'monkey' isnt a match for 'male'
    male_pattern = "(m[a-z]*)"
    female_pattern = "(f[a-z]*)"
    its_a_boy = re.match(male_pattern, gender, re.I)
    its_a_girl = re.match(female_pattern, gender, re.I)
    if its_a_boy is not None:
        return 'M'
    elif its_a_girl is not None:
        return 'F'
    else:
        # hermaphrodite? transgender?
        return None


def date_to_age_in_months(date):
    delta = datetime.date.today() - date
    #years = delta.days / 365.25
    return str(int(delta.days / 30.4375))


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
    except Exception as e:
        logging.info(e)
