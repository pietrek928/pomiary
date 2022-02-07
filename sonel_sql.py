from datetime import datetime
from sqlite3 import Cursor
from typing import Type, TypeVar, Generator

from pydantic import BaseModel


class Settings(BaseModel):
    property: str
    meterModel: str


class TreeValue(BaseModel):
    idNode: int
    property: int  # TODO: identify, create enum
    value: str


class Tree(BaseModel):
    idNode: int
    idParentNode: int  # for root = -1
    typeNode: int  # level ; 0 - root
    shortName: str
    name: str
    dateTime: datetime


class Measurement(BaseModel):
    """
    Measurements records
    """
    idMeasurement: int
    idNode: int
    typeMeasurement: str
    evaluate: str  # Correct, Unknown ; TODO: enum
    dateTime: datetime


class MeasurementValue(BaseModel):
    """
    Measurement properties by measurement id
    """
    idMeasurement: int
    property: str
    value: str


ModelType = TypeVar('ModelType')


def query_models(
        cur: Cursor, model: Type[ModelType],
        query_filter: str = '', order_by: str = ''
) -> Generator[ModelType, None, None]:
    field_names = tuple(model.__fields__.keys())
    fields_list = ', '.join(field_names)

    query = f'SELECT {fields_list} FROM {model.__name__}'
    if query_filter:
        query += f' WHERE {query_filter}'
    if order_by:
        query += f' ORDER BY {order_by}'

    for row in cur.execute(query):
        yield model(**dict(zip(field_names, row)))
