from typing import Dict, Iterable
import pandas as pd


def parse_energydetails(d: Dict) -> pd.DataFrame:
    def to_series(_d: Dict) -> Iterable[pd.Series]:
        for meter in _d['energyDetails']['meters']:
            name = meter['type']
            _df = pd.DataFrame.from_dict(meter['values'])
            if _df.empty:
                yield pd.Series(name=name)
                continue
            _df = _df.set_index('date')
            _df.index = pd.DatetimeIndex(_df.index)
            if _df.empty:
                yield pd.Series(name=name)
                continue
            ts = _df.value
            ts.name = name
            ts = ts.dropna()
            yield ts

    all_series = to_series(d)
    df = pd.concat(all_series, axis=1)
    return df
