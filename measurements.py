from collections import defaultdict
from sys import stderr
from typing import Tuple, Dict

from latex_utils import ContentItem, Math, MultiLine
from meas_render import MeasureDescriptor


def format_number(v, places):
    if v is None:
        return ''
    return '{:.{}f}'.format(round(v, places), places).replace('.', ',')


class PetlaZwarciaTNS(MeasureDescriptor):
    title: str = '(TN-C, TN-S) Badanie ochrony przed porażeniem przez samoczynne wyłączenie'
    measure_ids: Tuple[str, ...] = ('Zln', 'ZlpeRCD')

    def get_columns(self):
        return (
            'Wyłącznik', 'Typ',
            Math('I_n [A]'), Math('I_a [A]'),
            Math('Z_s [\\Omega]'), Math('Z_a [\\Omega]'),
            Math('I_k [A]'),
            'Ocena'
        )

    def format_row(self, data: Dict[str, Dict[str, str]]) -> Tuple[ContentItem, ...]:
        zln = data['Zln']
        # print(zln, file=stderr)
        fuse_model = zln['Type']
        fuse_characteristics = zln['FuseType']

        In = float(zln['In'][:-2])
        Ia = float(zln['ia.rawValue'])
        Zs = float(zln['zOhm.rawValue'])
        Za = 230. / Ia
        Ik = float(zln['ikA.rawValue'])
        # rOhm = str(round(float(zln['rOhm.rawValue']), 3))
        # xl = str(round(float(zln['xL.rawValue']), 3))

        return (
            fuse_model, fuse_characteristics,
            format_number(In, 2), format_number(Ia, 2),
            format_number(Zs, 2), format_number(Za, 2),
            format_number(Ik, 2), ''
        )


class TestRCD(MeasureDescriptor):
    title: str = 'Parametry zabezpieczeń różnicowoprądowych'
    measure_ids: Tuple[str, ...] = ('RCDAuto',)

    def _collect_results(self, meas_data):
        results = defaultdict(dict)
        for k, v in meas_data.items():
            if k.startswith('results.'):
                _, n, kk = k.split('.', 2)
                results[int(n)][kk] = v
        return tuple(tuple(zip(*sorted(results.items())))[1])

    def get_columns(self):
        return (
            MultiLine('Wyłącznik', 'RCD'),
            'Typ',
            MultiLine(Math('I_{\\Delta n}'), '[mA]'), MultiLine(Math('I_a'), '[mA]'),
            MultiLine(Math('t_a'), '[ms]'), MultiLine(Math('t_{RCD}'), '[ms]'),
            MultiLine(Math('U_d'), '[V]'), MultiLine(Math('U_I'), '[V]'),
            'Ocena'
        )

    def format_row(self, data: Dict[str, Dict[str, str]]) -> Tuple[ContentItem, ...]:
        RCDAuto = data['RCDAuto']
        results = self._collect_results(RCDAuto)
        print(len(results), file=stderr)

        trcd = None
        for v in results:
            if v['correctness'] == 'Correct' and v['RCDMeasureMode'] == 'taUbRe' and v['step'] == 'ta1+':
                trcd = float(v['t_a.rawValue']) * 1e3

        Ia = None
        for v in results:
            if v['correctness'] == 'Correct' and v['RCDMeasureMode'] == 'IaUbRe' and v['step'] == 'ia+':
                print(v, file=stderr)
                Ia = float(v['I_a.rawValue']) * 1e3

        rcd_model = RCDAuto['RCDTypeCombo']
        In_mA = float(RCDAuto['deltaInCombo'][:-3])

        UI = float(RCDAuto['ul.rawValue'])

        return (
            rcd_model, '',
            format_number(In_mA, 0), format_number(Ia, 0),
            '', format_number(trcd, 0),
            '', format_number(UI, 0), ''
        )
