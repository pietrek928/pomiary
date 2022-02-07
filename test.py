from pysqlite3 import connect

from latex_utils import Document, Ctx
from meas_render import format_measure_table
from measurements import PetlaZwarcia1Faz

conn = connect('sqlite/maluzyn.client')
cur = conn.cursor()

Document(
    header='\\captionsetup[table]{labelformat=empty}',
    packages=('longtable', 'caption', 'multirow', 'mathtools'),
    date='',
    title='pomiary',
    author='pietrek',
    body=format_measure_table(cur, PetlaZwarcia1Faz(), (3, 6)),
).render(Ctx())

# print(_get_measure_data(cur, (3, 6), ('Zln', 'ZlpeRCD')))
