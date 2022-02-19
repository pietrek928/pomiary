from pysqlite3 import connect

from latex_utils import Document, Ctx, Center, Content, MeasurePageSetup, MeasureTitlePage
from meas_render import format_measure_table
from measurements import TestRCD, PetlaZwarciaTNS

conn = connect('sqlite/maluzyn.client')
cur = conn.cursor()

Document(
    header=Content(
        MeasurePageSetup(),
        '\\captionsetup[table]{labelformat=empty}'
    ),
    packages=('longtable', 'caption', 'multirow', 'mathtools'),
    date='',
    title='pomiary',
    author='pietrek',
    body=Content(
        MeasureTitlePage(),
        Center(
            format_measure_table(cur, PetlaZwarciaTNS(), (3, 6)),
            format_measure_table(cur, TestRCD(), (3, 6)),
        ),
    )
).render(Ctx())

# print(_get_measure_data(cur, (3, 6), ('Zln', 'ZlpeRCD')))
