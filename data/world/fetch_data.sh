#!/bin/bash

mkdir src

# https://labor.ny.gov/stats/laus.asp
wget "https://labor.ny.gov/stats/lausCSV.asp?PASS=1&geog=21093561" -O src/unemployment.csv

# http://data.okfn.org/data/core/s-and-p-500
wget "http://data.okfn.org/data/core/s-and-p-500/r/data.csv" -O src/sp500.csv