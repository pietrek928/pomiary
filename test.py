from pysqlite3 import connect

from latex_utils import Document, Ctx, Center, Content, MeasurePageSetup, MeasureTitlePage, MeasureDescriptionPage, \
    IncludeFile, Attachment
from meas_render import format_measure_table
from measurements import TestRCD, PetlaZwarciaTNS

conn = connect('sqlite/maluzyn.client')
cur = conn.cursor()

Document(
    header=Content(
        MeasurePageSetup(firma='ElektroInf'),
        '\\captionsetup[table]{labelformat=empty}'
    ),
    packages=('longtable', 'caption', 'multirow', 'mathtools', 'svg'),
    date='',
    title='pomiary',
    author='pietrek',
    body=Content(
        MeasureTitlePage(firma='ElektroInf'),
        MeasureDescriptionPage(),
        Center(
            format_measure_table(cur, PetlaZwarciaTNS(), (3, 6)),
            format_measure_table(cur, TestRCD(), (3, 6)),
        ),
        IncludeFile(fname='akty-prawne.tex'),
        Attachment('aaaaaaaaaaaaaaa', name='ZZZZZałącznik'),
    )
).render(Ctx())

# print(_get_measure_data(cur, (3, 6), ('Zln', 'ZlpeRCD')))
