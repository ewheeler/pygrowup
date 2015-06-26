import logging
import os
import csv
import codecs
from decimal import Decimal as D

import nose

from . import pygrowup
from six.moves import zip


class WHOResult(object):
    def __init__(self, indicator, values):
        self.indicator = indicator
        columns = 'id,region,GENDER,agemons,WEIGHT,_HEIGHT,measure,oedema,HEAD,MUAC,TRI,SUB,SW,agedays,CLENHEI,CBMI,ZWEI,ZLEN,ZWFL,ZBMI,FWEI,FLEN,FWFL,FBMI'
        data = list(zip(columns.split(','), values))
        for k, v in data:
            setattr(self, k.lower(), v)
        self.age = self.agemons
        if int(self.gender) == 1:
            self.gender = "M"
        elif int(self.gender) == 2:
            self.gender = "F"
        else:
            self.gender = None

    def __repr__(self):
        rep = self.indicator + " " + str(self.id) + " " + self.agemons
        if all([self.gender, self.height]):
            rep = rep + " (" + ", ".join([self.gender, self.height]) + ")"
        return rep

    @property
    def result(self):
        if self.indicator == "lhfa":
            return self.zlen
        if self.indicator in ["wfl", "wfh"]:
            return self.zwfl
        if self.indicator == "wfa":
            return self.zwei
        if self.indicator == "bmifa":
            return self.zbmi

    @property
    def measurement(self):
        if self.indicator == "lhfa":
            return self._height
        if self.indicator in ["wfl", "wfh"]:
            return self.weight
        if self.indicator == "wfa":
            return self.weight
        if self.indicator == "bmifa":
            return self.cbmi

    @property
    def height(self):
        if self.indicator in ["lhfa", "wfl", "wfh", "wfa"]:
            return self._height
        return None


def compare_result(who):
    our_result = None
    logging.debug(who.indicator.upper() + " (" + str(who.measurement) + ") " + who.gender + " " + who.age + " " + str(who.height))
    calc = pygrowup.Calculator(include_cdc=True, log_level='DEBUG')
    if who.measurement:
        our_result = calc.zscore_for_measurement(who.indicator, who.measurement,
                                                 who.age, who.gender, who.height)
        logging.info("THEM: " + str(who.result))
        if who.result not in ['', ' ', None]:
            if our_result is not None:
                logging.info("US  : " + str(our_result))
                diff = calc.context.subtract(D(who.result), D(our_result))
                logging.info("DIFF: " + str(abs(diff)))
                assert abs(diff) <= D('1')


def test_generator():
    # software uses error-prone floating-point calculations
    module_dir = os.path.split(os.path.abspath(__file__))[0]
    test_file = os.path.join(module_dir, 'testdata', 'survey_z_rc.csv')
    csvee = codecs.open(test_file, "rU", encoding='utf-8', errors='ignore')

    reader = csv.reader(csvee, dialect="excel")
    # skip column labels
    next(reader)
    for row in reader:
        for indicator in ["lhfa", "wfl", "wfh"]:
            who = WHOResult(indicator, row)
            # ignore these two cases
            if who.id in ["287", "381"]:
                continue
            # also ignore other cases that are missing
            # height or length data required for these calculations
            if who.height not in ['', ' ', None]:
                yield compare_result, who
        for indicator in ["wfa", "bmifa"]:
            who = WHOResult(indicator, row)
            # ignore these two cases
            if who.id in ["287", "381"]:
                continue
            yield compare_result, who


def test_bmifa_bug():
    calc = pygrowup.Calculator(include_cdc=True, log_level='DEBUG')
    # test to verify fix of https://github.com/ewheeler/pygrowup/issues/6
    # where age of exactly 3 months would not be resolved to either
    # 0-13 week table or to 0-2 years table
    does_not_raise = calc.zscore_for_measurement('bmifa', 32.0,
                                                 3, 'F', 50)
    assert does_not_raise == D('7.41')

    should_use_bmifa_girls_0_13 = calc.zscore_for_measurement('bmifa', 32.0,
                                                              2.9, 'F', 50)
    assert should_use_bmifa_girls_0_13 == D('7.53')

    should_use_bmifa_girls_0_2 = calc.zscore_for_measurement('bmifa', 32.0,
                                                             3.1, 'F', 50)
    assert should_use_bmifa_girls_0_2 == D('7.41')

if __name__ == '__main__':
    nose.main()
