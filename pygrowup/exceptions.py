class PyGrowUpException(Exception):
    """Base class for exceptions in this library"""


class ImproperlySpecifiedAge(PyGrowUpException):
    """Raised when the age of an observation is improperly specified
    (as expressed in the child's age in days, months, or as two dates
    specifying date of birth and date of observation).
    """


class MissingAgeError(PyGrowUpException):
    """Raised when the age of an observation is not specified
    (as expressed in the child's age in days, months, or as two dates
    specifying date of birth and date of observation).
    """


class AgeOutOfRangeError(PyGrowUpException):
    """Raised when the age of an observation is not within the acceptable range
    for the indicator requested.
    """


class ImproperlySpecifiedSex(PyGrowUpException):
    """Raised when the sex of an observation's child is improperly specified.
    """


class ZScoreError(PyGrowUpException):
    """Raised when there's an unspecified problem determining a z-score"""


class ImproperlySpecifiedMeasurement(PyGrowUpException):
    """Raised when a measurement is not a valid numeric type.
    """

class MeasurementOutOfRangeError(PyGrowUpException):
    """Raised when a measurement falls outside of the *most generous* bounds
    for the indicator in question.
    """