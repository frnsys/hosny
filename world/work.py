"""
`p_offered` values sourced from Table 2 of:

    Offering a Job: Meritocracy and Social Networks. Trond Petersen, Ishak Saporta, Marc-David L. Seidel. AJS Volume 106 Number 3 (November 2000): 763-816.
    https://web.stanford.edu/group/scspi/_media/pdf/Reference%20Media/Petersen_Saporta_Seidel_2000_Social%20Networks.pdf

"""

import json
import random
import numpy as np
import pandas as pd

# this gives us monthly unemployment percentages for NY
monthly_df = pd.read_csv('data/world/src/unemployment.csv', index_col='Year')

# group by years
df = pd.read_csv('data/people/gen/pums_nyc.csv')
years = df.groupby('YEAR')

# offer probabilities
p_offer = json.load(open('data/world/gen/job_offer_probs.json', 'r'))

def income_bracket(code):
    """create income brackets for an income code"""
    bins = []
    df_max = df[code].max()
    df_min = df[code].min()

    # separate 0, negative, and positive values
    if df_min < 0:
        bins += list(np.arange(df_min, -1, 5000))
    bins += [0]

    # only go up to (max - 1) b/c max corresponds to N/A
    bins += list(np.arange(1, df_max - 1, 5000))
    bins += [df_max]
    return bins


income_codes = ['INCWAGE', 'INCINVST', 'INCWELFR', 'INCRETIR', 'INCBUS00', 'INCSS']
income_brackets = {code: income_bracket(code) for code in income_codes}


def employment_dist(year, month, sex, race):
    # return {'employed': 0.5, 'unemployed': 0.5}
    """probability of employment/unemployment
    given year, month (int, zero-indexed), sex, and race"""

    # prior is generated from monthly data
    prior_str = monthly_df.loc[year][month]
    prior_unemployed = float(prior_str[:-1])/100

    # likelihood is generated from PUMS individual data
    df_y = years.get_group(year)
    employed = df_y[df_y.EMPSTAT == 1]
    unemployed = df_y[df_y.EMPSTAT == 2]
    dist = {
        'employed': (employed, 1 - prior_unemployed),
        'unemployed': (unemployed, prior_unemployed)
    }
    for k, (df_k, prior) in dist.items():
        likelihood = 1.
        for col, var in [('SEX', sex), ('RACE', race)]:
            likelihood *= df_k[df_k[col] == var].size/df_k.size
        dist[k] = prior * likelihood

    # normalize to a distribution
    total = sum(dist.values())
    for group in dist.keys():
        dist[group] /= total
    return dist


def offer_prob(year, month, sex, race, referral, precomputed_emp_dist=None):
    """probability of a job offer
    referral keys: ['previous_contractor', 'other', 'headhunter_or_campus_recruiter', 'friend', 'ad_or_cold_call']
    race keys: ['nativeamerican', 'hispanic', 'black', 'asian', 'white']
    """
    if precomputed_emp_dist is not None:
        emp = precomputed_emp_dist[year][month - 1][race.name][sex.name]
    else:
        emp = employment_dist(year, month, sex, race)

    # quick-and-dirty mapping to race keys
    if not isinstance(race, str):
        if race.name == 'aian':
            race = 'nativeamerican'
        elif race.name == 'white':
            # b/c white and hispanic are merged together
            # TODO find dataset that separates these?
            race = random.choice(['hispanic', 'white'])
        elif race.name in ['chinese', 'japanese', 'api']:
            race = 'asian'
        elif race.name == 'black':
            race = 'black'

        # mean of two random races. this is a sloppy guess,
        # since the actual evidence may not work this way
        elif race.name in ['other', 'two', 'three_plus']:
            races = list(p_offer['offered']['race'].keys())
            op1 = _offer_prob(sex, random.choice(races), referral, emp)
            op2 = _offer_prob(sex, random.choice(races), referral, emp)
            return (op1 + op2)/2

    return _offer_prob(sex, race, referral, emp)


def _offer_prob(sex, race, referral, emp):
    p_o, p_no = p_offer['offered'], p_offer['not_offered']
    prob = p_o['sex'][sex.name] * p_o['race'][race] * p_o['referral'][referral] * emp['employed']
    not_prob = p_no['sex'][sex.name] * p_no['race'][race] * p_no['referral'][referral] * emp['unemployed']
    return prob/(prob + not_prob)


def income_change(from_year, to_year, sex, race, income_bracket, income_code):
    """samples a wage change between two years, based on the years, sex, and race"""
    lbound, ubound = income_bracket[1:-1].split(',')
    lbound, ubound = int(lbound), int(ubound)

    df_y = years.get_group(from_year)
    fr_group = df_y[df_y.EMPSTAT == 1][df_y.SEX == sex][df_y.RACE == race]
    fr_group = fr_group.groupby(pd.cut(fr_group[income_code], income_brackets[income_code]))
    fr_group = fr_group.get_group(income_bracket)

    df_y = years.get_group(to_year)
    to_group = df_y[df_y.EMPSTAT == 1][df_y.SEX == sex][df_y.RACE == race]
    to_group = to_group.groupby(pd.cut(to_group[income_code], income_brackets[income_code]))
    to_group = to_group.get_group(income_bracket)

    mean_diff = to_group[income_code].mean() - fr_group[income_code].mean()

    # tbh this is a pretty abritrary choice of standard deviation
    # need to revisit this
    return np.random.normal(mean_diff, abs((ubound-lbound)/2))


def job(year, sex, race, education):
    from people.generate import generate
    # sample a new person with this person's characteristics
    p = generate(year, {
        'sex': sex,
        'race': race,
        'education': education,
        'employed': 1
    })
    return {
        'wage_income': p['wage_income'],
        'wage_income_bracket': p['wage_income_bracket'],
        'occupation_code': p['occupation_code'],
        'occupation': p['occupation'],
        'industry_code': p['industry_code'],
        'industry': p['industry']
    }


def precompute_employment_dist():
    from people.attribs import Sex, Race

    emp_dist = {}
    for year in range(2005, 2014+1):
        yr = {}
        for month in range(0, 12):
            yr[month] = {}
            for race in Race:
                yr[month][race.name] = {}
                for sex in Sex:
                    yr[month][race.name][sex.name] = employment_dist(year, month, sex, race)
        emp_dist[year] = yr
    return emp_dist
