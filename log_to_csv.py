import json
import pandas as pd
from collections import defaultdict

data = defaultdict(list)

with open('simulation.log', 'r') as f:
    for line in f.readlines():
        line = line.strip()
        if line.startswith('graph'):
            entry = line.replace('graph:', '')
            entry = json.loads(entry)
            name = entry['graph']
            val = entry['data']['value']
            data[name].append(val)

df = pd.DataFrame.from_dict(data)
df.to_csv('data.csv')
