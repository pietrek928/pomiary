from collections import defaultdict
from random import uniform, choice
from typing import Iterable, Dict, Any


class ValueSampler:
    def __init__(self, values):
        n = len(values)
        if isinstance(values[0], (int, float)):
            avg = sum(values) / n
            var = (
                          sum((v - avg) ** 2 for v in values) / n
                  ) ** .5
            # if not var or n == 1:
            #     var = avg * .07
            self._min = avg - var
            self._max = avg + var
            self._values = None
        else:
            self._values = values

    def sample(self):
        if self._values:
            return choice(self._values)
        else:
            return uniform(self._min, self._max)


def get_samplers_for_items(items: Iterable[Dict[str, Any]]) -> Dict[str, ValueSampler]:
    vals = defaultdict(list)
    for item in items:
        for k, v in item.items():
            vals[k].append(v)
    if not vals:
        raise ValueError('No data found')
    return {
        prop_name: ValueSampler(prop_vals)
        for prop_name, prop_vals in vals.items()
    }


def sample_vals(samplers: Dict[str, ValueSampler], vals: Dict[str, Any]):
    return {
        prop_name: vals[prop_name] if prop_name in vals else samplers[prop_name].sample()
        for prop_name in set(samplers.keys()).union(vals.keys())
    }
