# pygrowup


pygrowup calculates z-scores for the growth measurements of children. The
indicators it supports are:

* weight-for-age
* length/height-for-age
* weight-for-length/height
* head circumference-for-age
* arm circumference-for-age (MUAC)
* BMI-for-age
* subscapular skinfold-for-age
* triceps skinfold-for-age

These are all based on the
[WHO Child Growth Standards](http://www.who.int/childgrowth/standards/en/)
(with the exception of MUAC for 5-19 years; see notes below about an additional
data source).

It has been tested on Python 2.7 and Python 3.5 & 3.6. (It in theory should work
on most earlier versions of Python 2 & 3.)

Thanks to GlobalStrategies for a JavaScript port!
* https://github.com/GlobalStrategies/jsgrowup
* published on npm as jsgrowup: https://www.npmjs.com/package/jsgrowup

Usage
=====

pygrowup is modelled based on an "observation" of a child. The age of the child
at the time of the observation is captured either explicitly, or inferred based
on the child's date of birth and the date of the observation. Once an Observation
object is instantiated, multiple methods are available to compute the z-scores
for the various indicators.

Examples:

    from datetime import date, timedelta
    from decimal import Decimal

    from pygrowup import Observation

    # Three ways of instantiating roughly comparable Observations for a
    # 13-month-old boy.
    today = date.today()
    thirteen_months_ago = today - timedelta(days=365 + 30)
    obs = Observation(sex=Observation.MALE, age_in_days=13*30)
    obs = Observation(sex=Observation.MALE, age_in_months=13)
    obs = Observation(sex=Observation.MALE, dob=thirteen_months_ago,
                      date_of_observation=today)

    # Now calculate some z-scores for this child
    print(obs.head_circumference_for_age(Decimal('46.5')))

    # Or, if you're into the whole brevity thing, each method has an alias. And
    # measurements can be expressed as ints, floats, or Decimals.
    print(obs.hcfa(46.5))  # Same result as the previous computation.

    print(obs.weight_for_age(Decimal('9.6')))
    print(obs.length_or_height_for_age(Decimal('77')))
    print(obs.weight_for_length(Decimal('9.6'), Decimal('77')))

Except for weight-for-length and weight-for-height, the z-score methods expect
a single argument for the measurement. (That means BMI must be calculated
separately (at least for now) and passed in as the measurement.)

Each method for calculating z-scores has a verbose name and a more succinct
alias. The full list of them (aliases in parentheses) is:

* arm\_circumference\_for\_age (acfa)
* bmi\_for\_age (bmifa)
* head\_circumference\_for\_age (hcfa)
* length\_or\_height\_for\_age (lhfa)
* subscapular\_skinfold\_for\_age (ssfa)
* triceps\_skinfold\_for\_age (tsfa)
* weight\_for\_age (wfa)
* weight\_for\_height (wfh)
* weight\_for\_length (wfl)

Differences from earlier versions of pygrowup
=========================
Some differences from the current version and version 0.8.1 and before are:

* This package employs precision based off of a child's age to the day-level
  where possible (up to 5 years of age); the original rounds to nearest
  completed month
* There is no CDC-data-based option for the growth metrics (at least for now)
* This package includes the more esoteric metrics (subscapular skinfold-for-age,
  triceps skinfold-for-age, arm circumference-for-age)

About tests
===========
Run the tests like this:

```python -m pygrowup.tests```

The tests run against two distinct datasets: one originating from the R
implementation of WHO's igrowup software, and the other based on data SPOON (see
credits) collected and processed using the Stata version of igrowup. Using the
WHO data, this package's z-scores are generally within 0.1 of the test datasets
with 2 exceptions. However, a number of results differ by at least 0.05. It's
not clear if that's due to the other implementations' use of floating point
arithmetic (in contrast with this package's use of python's Decimal library for
more precise computation) or if there are small inaccuracies in this
package. So, caveat emptor!

About MUAC data extension
=========================
The WHO dataset for mid-upper arm circumference only goes to 5 years. However,
it can be a useful proxy when weight is difficult to measure. Therefore, an
option is available to extend the range to 19 years by employing a dataset
[compiled by Lazarus Mramba, et al](http://www.bmj.com/content/358/bmj.j3423).
The data themselves were derived from
[a PDF from that publication](http://www.bmj.com/content/bmj/suppl/2017/08/03/bmj.j3423.DC1/mral036206.ww1.pdf).

Credits
=======

The initial implementation of this work was by [SPOON](http://www.spoonfoundation.org).
