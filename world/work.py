"""
`p_offered` values sourced from Table 2 of:

    Offering a Job: Meritocracy and Social Networks. Trond Petersen, Ishak Saporta, Marc-David L. Seidel. AJS Volume 106 Number 3 (November 2000): 763-816.
    https://web.stanford.edu/group/scspi/_media/pdf/Reference%20Media/Petersen_Saporta_Seidel_2000_Social%20Networks.pdf

"""

import json
import config
import numpy as np
import pandas as pd

# this gives us monthly unemployment percentages for NY
monthly_df = pd.read_csv('data/world/src/unemployment.csv', index_col='Year')

# group by years
df = pd.read_csv('data/people/gen/pums_nyc.csv')
years = df.groupby('YEAR')


# offer probabilities
p_offer = json.load(open('data/world/gen/job_offer_probs.json', 'r'))


def employment_dist(year, month, sex, race):
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


def offer_prob(year, month, sex, race, referral):
    """probability of a job offer"""
    emp = employment_dist(year, month, sex, race)
    p_o, p_no = p_offer['offered'], p_offer['not_offered']
    prob = p_o['sex'][sex.name] * p_o['race'][race.name] * p_o['referral'][referral] * emp['employed']
    not_prob = p_no['sex'][sex.name] * p_no['race'][race.name] * p_no['referral'][referral] * emp['unemployed']
    return prob/(prob + not_prob)


def income_change(from_year, to_year, sex, race, income_bracket):
    """samples a wage change between two years, based on the years, sex, and race"""
    lbound, ubound = income_bracket[1:-1].split(',')
    lbound, ubound = int(lbound), int(ubound)

    df_y = years.get_group(from_year)
    fr_group = df_y[df_y.EMPSTAT == 1][df_y.SEX == sex][df_y.RACE == race]
    fr_group = fr_group.groupby(pd.cut(fr_group.INCTOT, config.INCOME_BRACKETS))
    fr_group = fr_group.get_group(income_bracket)

    df_y = years.get_group(to_year)
    to_group = df_y[df_y.EMPSTAT == 1][df_y.SEX == sex][df_y.RACE == race]
    to_group = to_group.groupby(pd.cut(to_group.INCTOT, config.INCOME_BRACKETS))
    to_group = to_group.get_group(income_bracket)

    mean_diff = to_group.INCTOT.mean() - fr_group.INCTOT.mean()

    # tbh this is a pretty abritrary choice of standard deviation
    # need to revisit this
    return np.random.normal(mean_diff, abs((ubound-lbound)/2))


if __name__ == '__main__':
    from people.attribs import Sex, Race

    # pre-financial crisis
    print(employment_dist(2005, 5, Sex.male, Race.black))
    print(employment_dist(2005, 5, Sex.male, Race.white))

    # post-financial crisis
    print(employment_dist(2009, 5, Sex.male, Race.black))
    print(employment_dist(2009, 5, Sex.male, Race.white))

    print(income_change(2008, 2009, Sex.male, Race.black, '(20000, 25000]'))
    print(income_change(2008, 2009, Sex.male, Race.white, '(20000, 25000]'))
    print(income_change(2008, 2009, Sex.male, Race.api, '(20000, 25000]'))

    print(offer_prob(2005, 5, Sex.male, Race.white, 'friend'))
    print(offer_prob(2005, 5, Sex.male, Race.black, 'friend'))
