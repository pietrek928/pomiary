from collections import defaultdict
from typing import Tuple, Dict, Any

from pydantic import BaseModel
from pysqlite3 import Cursor

from latex_utils import LongTable, ContentItem, Bold
from sonel_sql import query_models, Tree, Measurement, MeasurementValue


class MeasureDescriptor(BaseModel):
    title: ContentItem = 'Pomiar'
    measure_ids: Tuple[str, ...] = ()

    def get_description(self) -> ContentItem:
        raise NotImplementedError('get description implemented')

    def get_columns(self) -> Tuple[ContentItem, ...]:
        raise NotImplementedError('get columns not implemented')

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        raise NotImplementedError('compute row not implemented')

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        raise NotImplementedError('get rows not implemented')


def get_measure_data(
        cur: Cursor, places: Tuple[Tree, ...], measure_types: Tuple[str, ...]
):
    place_ids_list = ", ".join(map(str, (place.idNode for place in places)))
    measure_types_list = ", ".join(f'"{m}"' for m in measure_types)
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
        places_by_ids[place_id].name or places_by_ids[place_id].idNode: {
            meas_type: meas_data for meas_type, meas_data in place_data.items()
        } for place_id, place_data in all_data.items()
    }


def _generate_measurements_rows(measure_descr: MeasureDescriptor, measure_data):
    for place_name, place_data in sorted(measure_data.items()):
        yield (place_name,) + measure_descr.format_row(place_data)


def format_measure_table(measure_descr: MeasureDescriptor, meas_data):
    return LongTable(
        caption=measure_descr.title,
        columns=('Badany punkt',) + measure_descr.get_columns(),
        rows=_generate_measurements_rows(measure_descr, meas_data),
    )


def format_legend(measure_descr: MeasureDescriptor):
    return Bold(measure_descr.title), measure_descr.get_description(), '\\quad', ''
