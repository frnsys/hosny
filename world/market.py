import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

df = pd.read_csv('data/world/gen/sp500.csv', index_col='Date', parse_dates=True)


def market_index(month, year, past_months=5):
    """market index (S&P500) for a given month and year and the specified past months.
    data sourced from <https://github.com/datasets/s-and-p-500>"""

    end = datetime(year=year, month=month, day=1)
    start = end + relativedelta(months=-past_months)
    return df.loc[start:end]['SP500']
