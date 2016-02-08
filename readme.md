# Humans of Simulated New York

(WIP)

You can generate a simulated New Yorker like so:

    from people import generate
    year = 2005
    person = generate(year)
    print(person)

    {
        'age': 36,
        'education': <Education.grade_12: 6>,
        'employed': <Employed.non_labor: 3>,
        'income': 3236,
        'income_bracket': '(1000, 5000]',
        'industry': 'Independent artists, performing arts, spectator sports, and related industrie
        s',
        'industry_code': 8560,
        'neighborhood': 'Greenwich Village',
        'occupation': 'Designer',
        'occupation_code': 2630,
        'puma': 3810,
        'race': <Race.white: 1>,
        'rent': 1155.6864868468731,
        'sex': <Sex.female: 2>,
        'year': 2005
    }

## Sources

- [Frequently Occurring Surnames from the Census 2000](http://www.census.gov/topics/population/genealogy/data/2000_surnames.html). Surnames occurring >= 100 more times in the 2000 census. Details here: <http://www2.census.gov/topics/genealogy/2000surnames/surnames.pdf>
- [Female/male first names from the Census 1990](http://deron.meranda.us/data/)
- Household and individual IPUMS data for 2005-2014, retrieved from [IPUMS USA, Minnesota Population Center, University of Minnesota](https://usa.ipums.org/usa/index.shtml)
- PUMS network map of NY, hand-compiled from <http://www.nyc.gov/html/dcp/pdf/census/puma_cd_map.pdf>
- NYC unemployment data was retrieved from [New York State Department of Labor](https://labor.ny.gov/stats/laus.asp)
- S&P500 data was retrieved from Open Knowledge's [Standard and Poor's (S&P) 500 Index Data including Dividend, Earnings and P/E Ratio](http://data.okfn.org/data/core/s-and-p-500)
