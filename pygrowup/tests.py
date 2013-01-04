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
        if self.gender == "1":
            self.gender = "M"
        elif self.gender == "2":
            self.gender = "F"
        else:
            self.gender = None

    def __repr__(self):
        rep = self.indicator + " " + str(self.id)
        if all([self.gender, self.agemons, self.height]):
            rep = rep + " (" + ", ".join([self.gender, self.agemons, self.height]) + ")"
        return rep

    @property
    def result(self):
        if self.indicator == "lhfa":
            return self.zlen
        if self.indicator in ["wfl", "wfh"]:
            return self.zwfl
        if self.indicator == "wfa":
            return self.zwei

    @property
    def measurement(self):
        if self.indicator == "lhfa":
            return self._height
        if self.indicator in ["wfl", "wfh"]:
            return self.weight
        if self.indicator == "wfa":
            return self.weight

    @property
    def height(self):
        if self.indicator in ["wfl", "wfh"]:
            return self._height
        return None


def compare_result(who):
    our_result = None
    #print who.indicator.upper() + " (" + str(who.measurement) + ") " + who.gender + " " + who.age + " " + str(who.height)
    pg = pygrowup.Growth()
    our_result = pg.zscore_for_measurement(who.indicator, who.measurement,
                                           who.age, who.gender, who.height)
    print "THEM: " + str(who.result)
    if who.result not in ['', ' ', None]:
        if our_result is not None:
            print "US  : " + str(our_result)
            diff = pg.context.subtract(D(who.result), D(our_result))
            assert abs(diff) <= D(1)


def test_generator():
    # software uses error-prone floating-point calculations
    module_dir = os.path.split(os.path.abspath(__file__))[0]
    test_file = os.path.join(module_dir, 'test.csv')
    csvee = codecs.open(test_file, "rU", encoding='utf-8', errors='ignore')

    reader = csv.reader(csvee, dialect="excel")
    for row in reader:
        for indicator in ["lhfa", "wfl", "wfh", "wfa"]:
            who = WHOResult(indicator, row)
            yield compare_result, who

if __name__ == '__main__':
    nose.main()
