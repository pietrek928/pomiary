from typing import Tuple, Dict

from latex_utils import ContentItem, Math
from meas_render import MeasureDescriptor


class PetlaZwarcia1Faz(MeasureDescriptor):
    title: str = 'Pomiar impedancji pętli zwarcia'
    measure_ids: Tuple[str, ...] = ('Zln', 'ZlpeRCD')

    def get_columns(self):
        return (
            '{Typ Bezpiecznika}', Math('I_n [A]'), Math('T_n [s]'),
            Math('I_{SC} [A]'), Math('R [\\Omega]'), Math('X_L [\\Omega]'),
        )

    def format_row(self, data: Dict[str, Dict[str, str]]) -> Tuple[ContentItem, ...]:
        zln = data['Zln']
        In_A = zln['In'][:-2]
        tn = zln['tn'][:-2]
        ika = str(round(float(zln['ikA.rawValue'])))
        rOhm = str(round(float(zln['rOhm.rawValue']), 3))
        xl = str(round(float(zln['xL.rawValue']), 3))

        return (
            zln['FuseType'], In_A, tn,
            ika, rOhm, xl
        )
