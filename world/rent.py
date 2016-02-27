"""
estimate a rent distribution and
probability of home ownership by neighborhood per year

this probably isn't very accurate, but other data for this
was surprisingly hard to find
"""

import random
import numpy as np
import pandas as pd
from util import random_choice
from scipy.stats import gaussian_kde

# prep the rent data
rent_dists = {}
df = pd.read_csv('data/world/gen/pums_household_nyc.csv')

# group by years
years = df.groupby('YEAR')

# for each year
for year in years.groups:
    rent_dists[year] = {}
    df_y = years.get_group(year)
    pumas = df_y.groupby('PUMA')
    for puma in pumas.groups:
        puma_dists = {}

        df_p = pumas.get_group(puma)
        total = df_p.size

        # https://usa.ipums.org/usa-action/variables/OWNERSHP#codes_section
        # 1 == ownership or in process of purchasing
        n_owned = df_p[df_p['OWNERSHP'] == 1].size
        puma_dists['p_owned'] = n_owned/total

        # https://usa.ipums.org/usa-action/variables/MORTGAGE#codes_section
        # 1 == ownership, "free and clear"
        n_owned_free = df_p[df_p['MORTGAGE'] == 1].size

        # 3, 4 == yes, mortgage or similar
        n_owned_mort = df_p[df_p['MORTGAGE'].isin([3,4])].size

        # https://usa.ipums.org/usa-action/variables/MORTGAG2#codes_section
        # 2, 3, 4, 5 == yes, second mortgage or home equity loan
        n_owned_mort2 = df_p[df_p['MORTGAG2'].isin([2,3,4,5])].size - n_owned_mort

        puma_dists['p_ownership'] = {
            'free': n_owned_free/n_owned,
            'mortgage1': n_owned_mort/n_owned,
            'mortgage2': n_owned_mort2/n_owned
        }

        # assume mortgages (monthly payments) are normally distributed
        mort1_arr = df_p[df_p['MORTGAGE'].isin([3,4])]['MORTAMT1'].as_matrix()
        puma_dists['mortgage1_dist'] = gaussian_kde(mort1_arr)
        mort2_arr = df_p[df_p['MORTGAG2'].isin([2,3,4,5])]['MORTAMT2'].as_matrix()
        try:
            puma_dists['mortgage2_dist'] = gaussian_kde(mort2_arr)
        except np.linalg.linalg.LinAlgError:
            puma_dists['mortgage2_dist'] = np.mean(mort2_arr)
        except ValueError:
            puma_dists['mortgage2_dist'] = 0 if not mort2_arr else np.mean(mort2_arr)

        # assume rent is normally distributed
        rent_arr = df_p[df_p['RENT'] != 0]['RENT'].as_matrix()
        puma_dists['rent_dist'] = gaussian_kde(rent_arr)

        rent_dists[year][puma] = puma_dists


def sample_rent(year, puma):
    """generates a plausible rent amount (here, rent can mean a monthly mortgage payment)
    given a year and a PUMA"""
    rent = 0
    rent_info = rent_dists[year][puma]
    if random.random() < rent_info['p_owned']:
        ownership = random_choice(rent_info['p_ownership'].items())
        if ownership == 'free':
            rent = 0
        elif ownership == 'mortgage1':
            rent = rent_info['mortgage1_dist'].resample(1)[0][0]
        elif ownership == 'mortgage2':
            try:
                rent += rent_info['mortgage2_dist'].resample(1)[0][0]
            except AttributeError:
                rent += rent_info['mortgage2_dist']
    else:
        rent = rent_info['rent_dist'].resample(1)[0][0]
    return rent
