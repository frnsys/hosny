"""
lookup description and codes (if available) for PUMS columns
"""

import re
import sys
import json
import requests


columns = {
    'TRANWORK': {
        'desc': 'Transportation to work',
    },
    'PWPUMA00': {
        'desc': 'Place of work (PUMA)',
    },
    'TRANTIME': {
        'desc': 'Travel time to work',
    },
    'DEPARTS': {
        'desc': 'Time of departure for work',
    },
    'ARRIVES': {
        'desc': 'Time of arrival at work',
    },
    'CRIME': {
        'desc': 'Crime',
    },
    'VETSTAT': {
        'desc': 'Veteran status',
    },
    'DIFFREM': {
        'desc': 'Cognitive difficulty',
    },
    'DIFFPHYS': {
        'desc': 'Ambulatory difficulty',
    },
    'DIFFMOB': {
        'desc': 'Independent living difficulty',
    },
    'DIFFCARE': {
        'desc': 'Self-care difficulty',
    },
    'DIFFSENS': {
        'desc': 'Vision or hearing difficulty',
    },
    'MIGPLAC1': {
        'desc': 'State or country of residence 1 year ago',
    },
    'INCTOT': {
        'desc': 'Total personal income',
    },
    'FTOTINC': {
        'desc': 'Total family income',
    },
    'INCWAGE': {
        'desc': 'Wage and salary income',
    },
    'INCBUS00': {
        'desc': 'Business and farm income',
    },
    'INCSS': {
        'desc': 'Social security income',
    },
    'INCWELFR': {
        'desc': 'Welfare (public assistance) income',
    },
    'INCINVST': {
        'desc': 'Interest, dividend, and rental income',
    },
    'INCRETIR': {
        'desc': 'Retirement income',
    },
    'INCSUPP': {
        'desc': 'Supplemnetary security income',
    },
    'INCOTHER': {
        'desc': 'Other income',
    },
    'INCEARN': {
        'desc': 'Total personal earned income',
    },
    'POVERTY': {
        'desc': 'Poverty status',
    },
    'EMPSTAT': {
        'desc': 'Employment status',
    },
    'LABFORCE': {
        'desc': 'Labor force status',
    },
    'OCC': {
        'desc': 'Occupation',
    },
    'OCC2010': {
        'desc': 'Occupation, 2010 basis',
    },
    'IND': {
        'desc': 'Industry',
    },
    'IND1990': {
        'desc': 'Industry, 1990 basis',
    },
    'CLASSWKR': {
        'desc': 'Class of worker (e.g. self-employed or not)',
    },
    'OCCSOC': {
        'desc': 'Occupation, SOC classification',
    },
    'INDNAICS': {
        'desc': 'Industry, NAICS classification',
    },
    'WKSWORK2': {
        'desc': 'Weeks worked last year, intervalled',
    },
    'UHRSWORK': {
        'desc': 'Usual hours worked per week',
    },
    'LOOKING': {
        'desc': 'Looking for work',
    },
    'AVAILBLE': {
        'desc': 'Available for work',
    },
    'EDUC': {
        'desc': 'Educational attainment',
    },
    'GRADEATT': {
        'desc': 'Grade level attending',
    },
    'SCHLTYPE': {
        'desc': 'Public or private school',
    },
    'DEGFIELD': {
        'desc': 'Field of degree',
    },
    'DEGFIELD2': {
        'desc': 'Field of second degree (if any)',
    },
    'SCHOOL': {
        'desc': 'School attendance',
    },
    'HCOVANY': {
        'desc': 'Any health insurance coverage',
    },
    'HCOVPRIV': {
        'desc': 'Private health insurance coverage',
    },
    'HINSEMP': {
        'desc': 'Health insurance through employer/union',
    },
    'HINSPUR': {
        'desc': 'Health insurance purchased directly',
    },
    'HCOVPUB': {
        'desc': 'Public health insurance coverage',
    },
    'HINSCAID': {
        'desc': 'Health insurance through Medicaid',
    },
    'HINSCARE': {
        'desc': 'Health insurance through Medicare',
    },
    'HINSVA': {
        'desc': 'Health insurance through VA',
    },
    'HINSTRI': {
        'desc': 'Health insurance through TRICARE',
    },
    'HINSIHS': {
        'desc': 'Health insurance through Indian Health Services',
    },
    'RACE': {
        'desc': 'Race',
    },
    'BPL': {
        'desc': 'Birthplace',
    },
    'CITIZEN': {
        'desc': 'Citizenship status',
    },
    'SPEAKENG': {
        'desc': 'Speaks English',
    },
    'SEX': {
        'desc': 'Sex',
    },
    'AGE': {
        'desc': 'Age',
    },
    'BIRTHYR': {
        'desc': 'Year of birth',
    },
    'MARRNO': {
        'desc': 'Times married',
    },
    'DIVINYR': {
        'desc': 'Divorced in the past year',
    },
    'WIDINYR': {
        'desc': 'Widowed in the past year',
    },
    'FERTYR': {
        'desc': 'Children born within the last year',
    },
    'PUMA': {
        'desc': 'Public Use Microdata Area',
    },
    'PUMARES2MIG': {
        'desc': 'Public Use Microdata Area matching MIGPUMA',
    },
    'CITY': {
        'desc': 'City',
    },
    'CITYPOP': {
        'desc': 'City population',
    },
    'COUNTY': {
        'desc': 'County',
    },
    'COUNTYFIPS': {
        'desc': 'County (FIPS code)'
    },
}

# bleh, to ignore the requests cert warning
import warnings
warnings.filterwarnings("ignore")

cat_data_re = re.compile(r'categories:(.+)')

if __name__ == '__main__':
    colnam = sys.argv[1]
    column = columns.get(colnam)
    if column is None:
        print('Couldn\'t find a column named "{}"'.format(colnam))
        sys.exit(1)
    print('~~~')
    print(colnam)
    print(column['desc'])

    codes_url = 'https://usa.ipums.org/usa-action/variables/{}#codes_section'.format(colnam)
    resp = requests.get(codes_url, verify=False) # they have an outdated cert or something? skip verification

    try:
        # literally pull out the javascript code which specifies the category data
        json_data = cat_data_re.search(resp.text).group(1).strip(',')
        data = json.loads(json_data)
        for item in data:
            if item['code'] is not None:
                print(item['code'], ':', item['label'])
    except AttributeError:
        print('Couldn\'t find extractable code reference, but you can look it up yourself here:')
        print(codes_url)


