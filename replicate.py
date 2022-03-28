from re import sub
from typing import Iterable

from pysqlite3 import Cursor

from meas_render import MeasureDescriptor, get_measure_data
from sonel_sql import query_tree_children
from value_sampler import get_samplers_for_items, sample_vals


def name_to_pattern(name):
    pattern = sub(r"\d+", "XXX", name)
    assert pattern.count('XXX') == 1
    return pattern


def fill_pattern(pattern, nums):
    return tuple(
        pattern.replace('XXX', str(n))
        for n in nums
    )


def fill_for_node(cur: Cursor, node_id: int, meas: MeasureDescriptor, names: Iterable[str] = ()):
    children = tuple(query_tree_children(cur, (node_id,)))

    db_data = get_measure_data(cur, children, meas.measure_ids)
    extracted_data = {
        node_id: meas.compute_row(data)
        for node_id, data in db_data.items()
    }

    samplers = get_samplers_for_items(extracted_data.values())

    return {
        place_name: sample_vals(
            samplers, extracted_data.get(place_name) or {}
        ) for place_name in set(names).union(db_data.keys())
    }