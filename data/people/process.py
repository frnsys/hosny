"""
processes individual PUMS data for the years 2005-2014.
data was retrieved from:

    IPUMS USA, Minnesota Population Center, University of Minnesota
    https://usa.ipums.org/usa/index.shtml
"""

import pandas as pd

df = pd.read_csv('src/pums.csv')

# 4610 (New York, NY)
# 4611 (Brooklyn, NY)
ny_cities = [4610, 4611]
df = df[df.CITY.isin(ny_cities)]

# don't care about these
df = df.drop(['DATANUM', 'SERIAL', 'HHWT', 'COUNTY', 'COUNTYFIPS', 'CITY', 'GQ', 'PERNUM', 'PERWT'], axis=1)

# these are unnecessary/redundant (some can be estimated from other columns)
# note that some columns have the regular column name
# and another column with 'D' after the name - this is the _detailed_ version
# of that column, which has more specific codes.
# for example, 'EDUC' and 'EDUCD'.
df = df.drop(['BIRTHYR', 'BIRTHQTR', 'RACED', 'VETSTATD', 'FERTYR',
              'EMPSTATD', 'GRADEATT', 'GRADEATTD', 'EDUCD', 'BPLD',
              'CLASSWKRD', 'LABFORCE', 'CITIZEN', 'WKSWORK2',
              'UHRSWORK', 'LOOKING', 'AVAILBLE', 'FTOTINC',
              'OCC', 'IND1990', 'PUMARES2MIG', 'POVERTY'], axis=1)

# drop these b/c they may be too detailed for our purposes
df = df.drop(['INCWAGE', 'INCBUS00', 'INCOTHER', 'INCEARN', 'INCINVST',
              'INCRETIR', 'INCSUPP', 'INCSS', 'INCWELFR'], axis=1)

# drop these b/c they are object datatype
df = df.drop(['INDNAICS', 'OCCSOC'], axis=1)

# drop these b/c they are not present in all years.
df = df.drop(['MARRNO', 'DIVINYR', 'WIDINYR', 'HCOVANY', 'HCOVPRIV', 'HINSEMP',
              'HINSPUR', 'HINSTRI', 'HCOVPUB', 'HINSCAID', 'HINSCARE', 'HINSVA',
              'HINSIHS', 'DEGFIELD', 'DEGFIELDD', 'DEGFIELD2', 'DEGFIELD2D'], axis=1)

# temporarily removing these, would like to add them back in later
df = df.drop(['VETSTAT', 'DIFFREM', 'DIFFPHYS', 'DIFFMOB', 'DIFFCARE', 'DIFFSENS', 'SPEAKENG'], axis=1)

# group by years
years = df.groupby('YEAR')

print('years:', df['YEAR'].unique())

print('sample size per year:')
print(years.size())

# print which columns are missing for which years
year_dfs = [(year, years.get_group(year)) for year in years.groups]
for y, df_y in year_dfs:
    null_cols = [col for col in df_y.columns if df_y[col].isnull().any()]
    if null_cols:
        print(y, 'is missing the following columns:')
        print(null_cols)

# build data for transit model
transit_df = df[['PUMA', 'PWPUMA00', 'TRANWORK', 'TRANTIME', 'DEPARTS', 'ARRIVES']]
transit_df = transit_df[transit_df['PWPUMA00'] != 0]
transit_df.rename(columns={
    'PUMA':     'from_puma',
    'PWPUMA00': 'to_puma',
    'TRANWORK': 'transit',
    'TRANTIME': 'time',
    'DEPARTS':  'departs',
    'ARRIVES':  'arrives'
}, inplace=True)
transit_df.to_csv('gen/pums_nyc_transit.csv', index=False)

df = df.drop(['TRANTIME', 'ARRIVES'], axis=1)
df.to_csv('gen/pums_nyc.csv', index=False)

print('Using columns:', df.columns)
