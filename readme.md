# Humans of Simulated New York

This is an (in-progress) New York City simulator.

Using Census and other data (see below for references), a population of plausible simulated New Yorkers are generated and distributed through the simulated city. They live their lives day to day, trying their best, as the world around them changes according to historical data points (unemployment rates, market data, etc) from 2005 to 2014.

A static demo can be explored with here: [Public Science Agency](http://pubsci.agency)

---

You can generate a simulated New Yorker like so:

    from people import generate
    year = 2005
    person = generate(year)
    print(person)

    {
        'age': 36,
        'education': <Education.grade_12: 6>,
        'employed': <Employed.non_labor: 3>,
        'wage_income': 3236,
        'wage_income_bracket': '(1000, 5000]',
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

## Technical details

Individual-level New Yorker data (see the IPUMS resources below) is used to learn a Bayes Net that then is sampled to generate simulated New Yorkers. Thus the generated New Yorkers are "plausible" in that correlations that exist in the real world are reflected in them.

Each New Yorker is designed as an (expected) utility-maximizing agent. They are configured with some utility functions (determining how much, for example, stress bothers them, and how happy money makes them), some possible actions (such as working or sleeping), and goals (such as paying the rent). Overtime, they may make new goals as well. Each day they make a plan for that day (for speed, this is a simple hill-climbing search algorithm) and try to their best to accomplish it.

Simulated New Yorkers also have their own social networks - based on the model used in [this study](http://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=1254&context=sociologyfacpub), two simulated New Yorkers may become friends by some chance, depending on their similarity. This affects things like their ability to find employment.

As days go by, the world environment changes according to real historical data; this can have an effect on the simulated New Yorkers. For instance, when unemployment rates are up, they have a higher chance of losing their job (depending on factors such as their race and sex; these correlations are also derived from real data).

## Usage

### Setup

First setup your virtual environment and install the requirements:

    pip install -r requirements.txt

We also need `cess`:

    git clone https://github.com/frnsys/cess.git
    cd cess
    pip install --editable .

And `handlebars`:

    npm install -g handlebars

Then compile the JS templates:

    cd app/static/js
    bash compile

### Running

(run each of the following in separate tabs)

    # run redis
    redis-server

    # run the server
    python app.py

    # run the celery worker
    # only run one celery process; this is a bit of a hack to ensure that
    # only one City model is created and we step only that model
    celery -A app.tasks.celery worker --concurrency=1

Then visit `http://localhost:5000`.

You'll be presented with a screen which provides some basic world configuration options. Hit "Let's Start" and you'll be taken to the main simulation screen. Hit "Start Month" to run one month of the simulation.

### Data

Running the simulation will generate a log file at `simulation.log`. You can run the provided `log_to_csv.py` script to process this into a CSV of the simulation data.

## Sources

- [Frequently Occurring Surnames from the Census 2000](http://www.census.gov/topics/population/genealogy/data/2000_surnames.html). Surnames occurring >= 100 more times in the 2000 census. Details here: <http://www2.census.gov/topics/genealogy/2000surnames/surnames.pdf>
- [Female/male first names from the Census 1990](http://deron.meranda.us/data/)
- Household and individual IPUMS data for 2005-2014, retrieved from [IPUMS USA, Minnesota Population Center, University of Minnesota](https://usa.ipums.org/usa/index.shtml)
- PUMS network map of NY, hand-compiled from <http://www.nyc.gov/html/dcp/pdf/census/puma_cd_map.pdf>
- NYC unemployment data was retrieved from [New York State Department of Labor](https://labor.ny.gov/stats/laus.asp)
- S&P500 data was retrieved from Open Knowledge's [Standard and Poor's (S&P) 500 Index Data including Dividend, Earnings and P/E Ratio](http://data.okfn.org/data/core/s-and-p-500)
- Friendship model parameters were taken from [Social Distance in the United States: Sex, Race, Religion, Age, and Education Homophily among Confidants, 1985 to 2004. Jeffrey A. Smith, Miller McPherson, Lynn Smith-Lovin. University of Nebraska - Lincoln. 2014.](http://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=1254&context=sociologyfacpub)
- `annual_expenses.json` were taken from [Living Wage Calculator](http://livingwage.mit.medu/counties/36061) (Amy K. Glasmeier, Carey Anne Nadeau, Eric Schultheis, 2014)
