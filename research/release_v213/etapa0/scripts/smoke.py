import sys, site
import cyclophaser, cmocean, numpy, pandas, scipy, matplotlib
f = cyclophaser.__file__
assert sys.prefix in f and "site-packages" in f, f"NOT FROM VENV: {f}"
print("cyclophaser.__file__", f)
from importlib.metadata import version
for p in ["cyclophaser","cmocean","numpy","pandas","scipy","matplotlib","xarray"]:
    print(p, version(p))
import pandas as pd
from cyclophaser import determine_periods, example_file
df = pd.read_csv(example_file, parse_dates=[0], delimiter=';', index_col=[0])
r = determine_periods(df.iloc[:,-1].to_list(), x=df.index)
print("determine_periods OK, rows:", len(r), "columns:", list(r.columns)[:6])
