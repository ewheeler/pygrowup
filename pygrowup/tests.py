import os
import csv
import codecs
from decimal import Decimal as D

import nose

import pygrowup


class WHOResult(object):
    def __init__(self, indicator, values):
        self.indicator = indicator
        columns = 'id,region,GENDER,agemons,WEIGHT,_HEIGHT,measure,oedema,HEAD,MUAC,TRI,SUB,SW,agedays,CLENHEI,CBMI,ZWEI,ZLEN,ZWFL,ZBMI,FWEI,FLEN,FWFL,FBMI'
        data = zip(columns.split(','), values)
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
    #print who.indicator.upper() + " (" + str(who.measurement) + ") " + who.gender + " " + who.age + " " + str(who.height)
    calc = pygrowup.Calculator(include_cdc=True, log_level='DEBUG')
    if who.measurement:
        our_result = calc.zscore_for_measurement(who.indicator, who.measurement,
                                                 who.age, who.gender, who.height)
        print "THEM: " + str(who.result)
        if who.result not in ['', ' ', None]:
            if our_result is not None:
                print "US  : " + str(our_result)
                diff = calc.context.subtract(D(who.result), D(our_result))
                print "DIFF: " + str(abs(diff))
                assert abs(diff) <= D('1')


def test_generator():
    # software uses error-prone floating-point calculations
    module_dir = os.path.split(os.path.abspath(__file__))[0]
    test_file = os.path.join(module_dir, 'testdata', 'survey_z_rc.csv')
    csvee = codecs.open(test_file, "rU", encoding='utf-8', errors='ignore')

    reader = csv.reader(csvee, dialect="excel")
    # skip column labels
    reader.next()
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

if __name__ == '__main__':
    nose.main()
