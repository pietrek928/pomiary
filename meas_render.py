from collections import defaultdict
from sqlite3 import Cursor
from typing import Tuple, Dict

from pydantic import BaseModel

from latex_utils import LongTable, ContentItem
from sonel_sql import query_models, Tree, Measurement, MeasurementValue


class MeasureDescriptor(BaseModel):
    title: ContentItem = 'Pomiar'
    measure_ids: Tuple[str, ...] = ()

    def get_columns(self) -> Tuple[ContentItem, ...]:
        raise NotImplementedError('get columns not implemented')

    def format_row(self, data: Dict[str, Dict[str, str]]) -> Tuple[ContentItem, ...]:
        raise NotImplementedError('get rows not implemented')


def _get_measure_data(
        cur: Cursor, place_ids: Tuple[int, ...], measure_types: Tuple[str, ...]
):
    place_ids_list = ", ".join(map(str, place_ids))
    measure_types_list = ", ".join(f'"{m}"' for m in measure_types)
    places = query_models(
        cur, Tree, query_filter=f'idNode IN ({place_ids_list})'
    )
    places_by_ids = {}
    for place in places:
        places_by_ids[place.idNode] = place

    measurements = query_models(
        cur, Measurement,
        query_filter=f'idNode IN ({place_ids_list}) AND typeMeasurement IN ({measure_types_list}) AND evaluate = "Correct"',
        order_by='dateTime ASC'
    )
    meas_by_ids = {}
    meas_unique = {}
    all_data = defaultdict(lambda: defaultdict(dict))
    for meas in measurements:
        meas_unique[(meas.idNode, meas.typeMeasurement)] = meas.idMeasurement
        meas_by_ids[meas.idMeasurement] = meas
        all_data[meas.idNode][meas.typeMeasurement]['place_name'] = places_by_ids[meas.idNode].shortName

    measure_ids_list = ", ".join(map(str, meas_unique.values()))
    measurement_values = query_models(
        cur, MeasurementValue,
        query_filter=f'idMeasurement IN ({measure_ids_list})',
    )

    for v in measurement_values:
        meas = meas_by_ids[v.idMeasurement]
        all_data[meas.idNode][meas.typeMeasurement][v.property] = v.value

    return {
        place_id: {
            meas_type: meas_data for meas_type, meas_data in place_data.items()
        } for place_id, place_data in all_data.items()
    }


def _generate_measurements_rows(measure_descr: MeasureDescriptor, measure_data):
    for place_id, place_data in sorted(measure_data.items()):
        place_name = next(iter(place_data.values()))['place_name']
        yield (place_name,) + measure_descr.format_row(place_data)


def format_measure_table(cur: Cursor, measure_descr: MeasureDescriptor, place_ids: Tuple[int, ...]):
    meas_data = _get_measure_data(cur, place_ids, measure_descr.measure_ids)
    return LongTable(
        caption=measure_descr.title,
        columns=('Miejsce',) + measure_descr.get_columns(),
        rows=_generate_measurements_rows(measure_descr, meas_data),
    )
