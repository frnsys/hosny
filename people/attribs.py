from enum import IntEnum


class Sex(IntEnum):
    """https://usa.ipums.org/usa-action/variables/SEX#codes_section"""
    male = 1
    female = 2


class Race(IntEnum):
    """https://usa.ipums.org/usa-action/variables/RACE#codes_section"""
    white      = 1  # note that hispanic falls under "white"
    black      = 2
    aian       = 3  # american indian or alaskan native
    chinese    = 4
    japanese   = 5
    api        = 6  # other asian or pacific islander
    other      = 7  # "other race"
    two        = 8  # "two major races"
    three_plus = 9  # "three or more major races"


class Education(IntEnum):
    """https://usa.ipums.org/usa-action/variables/EDUC#codes_section"""
    none                        = 0
    preschool_through_grade_4   = 1
    grade_5_through_8           = 2
    grade_9                     = 3
    grade_10                    = 4
    grade_11                    = 5
    grade_12                    = 6
    college_1                   = 7
    college_2                   = 8
    college_3                   = 9
    college_4                   = 10
    college_5_or_more           = 11


class Employed(IntEnum):
    """https://usa.ipums.org/usa-action/variables/EMPSTAT#codes_section"""
    none        = 0
    employed    = 1
    unemployed  = 2
    non_labor   = 3 # not in labor force


class Employer(IntEnum):
    """https://usa.ipums.org/usa-action/variables/CLASSWKR#codes_section"""
    none        = 0
    self        = 1
    someone     = 2 # "works for wages"
