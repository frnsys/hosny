"""
processes household PUMS data for the years 2005-2014.
data was retrieved from:

    IPUMS USA, Minnesota Population Center, University of Minnesota
    https://usa.ipums.org/usa/index.shtml
"""

import pandas as pd

df = pd.read_csv('src/pums_household.csv')

print(df.columns)

# 4610 (New York, NY)
# 4611 (Brooklyn, NY)
ny_cities = [4610, 4611]
df = df[df.CITY.isin(ny_cities)]

print(len(df))

# group by years
years = df.groupby('YEAR')

print('years:', df['YEAR'].unique())

print('sample size per year:')
print(years.size())

df.to_csv('gen/pums_household_nyc.csv', index=False)
