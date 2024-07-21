from collections import defaultdict
from sys import stderr
from typing import Tuple, Dict, Any

from latex_utils import ContentItem, Math, MultiLine, Content, Color
from meas_render import MeasureDescriptor


def format_number(v, places, max_value=None):
    if v is None:
        return ''
    if max_value and v > max_value:
        return '> {:.{}f}'.format(round(max_value, places), places).replace('.', ',')
    return '{:.{}f}'.format(round(v, places), places).replace('.', ',')


# POZYTYWNA = Color(color='magenta', text='Pozytywna')
POZYTYWNA = 'Pozytywna'
NEGATYWNA = Color(color='red', text='Negatywna')


class PetlaZwarciaTNS(MeasureDescriptor):
    title: str = 'Badanie ochrony przed porażeniem przez samoczynne wyłączenie'
    measure_ids: Tuple[str, ...] = ('Zln', 'ZlpeRCD')

    def get_description(self) -> ContentItem:
        return (
            # 'Wyłącznik: nazwa elementu zabezpieczającego obwód',
            'Typ: charakterystyka bezpiecznika',
            Content(Math('I_n [A]'), ': prąd nominalny bezpiecznika'),
            Content(Math('I_a [A]'), ': prąd powodujący wyzwolenie bezpiecznika'),
            Content(Math('Z_s [\\Omega]'), ': zmierzona wartość impedancji pętli zwarcia: '),
            Content(Math('Z_a [\\Omega]'), ': wymagana wartość impedancji pętli zwarcia: ', Math('Z_a = U_o / I_a')),
            Content(Math('I_k [A]'), ': prąd zwarcia wyliczony: ', Math('I_k = U_o / Z_s')),
            Content('Ocena: ocena pomiaru - pozytywna gdy ', Math('Z_s <= Z_a')),
        )

    def get_columns(self):
        return (
            # 'Wyłącznik',
            'Typ',
            Math('I_n [A]'), Math('I_a [A]'),
            Math('Z_s [\\Omega]'), Math('Z_a [\\Omega]'),
            Math('I_k [A]'),
            'Ocena'
        )

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        # rOhm = str(round(float(zln['rOhm.rawValue']), 3))
        # xl = str(round(float(zln['xL.rawValue']), 3))
        zln = data['Zln']
        return dict(
            fuse_model=zln['Type'],
            fuse_characteristics=zln['FuseType'],
            In=float(zln['In'][:-2]),
            Ia=float(zln['ia.rawValue']),
            Zs=float(zln['zOhm.rawValue']),
            # Ik=float(zln['ikA.rawValue']),
        )

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        Za = 230. / row['Ia']
        Ik = 230. / row['Zs']
        return (
            # row['fuse_model'],
            row['fuse_characteristics'],
            format_number(row['In'], 2), format_number(row['Ia'], 2),
            format_number(row['Zs'], 2), format_number(Za, 2),
            format_number(Ik, 2), POZYTYWNA if row['Zs'] <= Za else NEGATYWNA
        )


class TestRCD(MeasureDescriptor):
    title: str = 'Parametry zabezpieczeń różnicowoprądowych'
    measure_ids: Tuple[str, ...] = ('RCDAuto',)

    def get_description(self) -> ContentItem:
        return (
            'Wyłącznik RCD: nazwa elementu zabezpieczającego obwód',
            'Typ: charakterystyka zabezpieczenia',
            Content(Math('I_{\\Delta n} [mA]'), 'róznicowy prąd wyłączający'),
            Content(Math('I_a [mA]'), 'prąd wyłaczający RCD'),
            Content(Math('ta [ms]'), 'wymagany czas wyłączenia RCD'),
            Content(Math('t_{RCD} [ms]'), 'wymagany czas wyłączenia RCD'),
            Content(Math('U_d [V]'), 'napięcie dotykowe zmierzone'),
            Content(Math('U_I [V]'), 'dopuszczalne napięcie dotykowe bezpiecznie'),
            Content(
                'Ocena: dopuszczalne napięcie dotykowe bezpiecznie ',
                Math('U_d <= U_I'), Math('t_{RCD} <= t_A'), Math('1/2 I_dn < I_a < I_dn'),
            ),
        )

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

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        RCDAuto = data['RCDAuto']
        results = self._collect_results(RCDAuto)

        row = {}

        for v in results:
            if v['correctness'] == 'Correct' and v['RCDMeasureMode'] == 'taUbRe' and v['step'] == 'ta1+':
                row['trcd'] = float(v['t_a.rawValue']) * 1e3

        for v in results:
            if v['correctness'] == 'Correct' and v['RCDMeasureMode'] == 'IaUbRe' and v['step'] == 'ia+':
                print(v, file=stderr)
                row['Ia'] = float(v['I_a.rawValue']) * 1e3

        row.update(
            rcd_model=RCDAuto['RCDTypeCombo'],
            In_mA=float(RCDAuto['deltaInCombo'][:-3]),
            UI=float(RCDAuto['ul.rawValue']),
        )
        print(row, file=stderr)
        return row

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        return (
            row['rcd_model'], '',
            format_number(row['In_mA'], 0), format_number(row['Ia'], 0),
            '', format_number(row['trcd'], 0),
            '', format_number(row['UI'], 0), ''
        )


class TestRCDta(MeasureDescriptor):
    title: str = 'Parametry zabezpieczeń różnicowoprądowych'
    measure_ids: Tuple[str, ...] = ('RCDta',)

    def get_description(self) -> ContentItem:
        return (
            # 'Wyłącznik RCD: nazwa elementu zabezpieczającego obwód',
            'Typ: charakterystyka zabezpieczenia',
            Content(Math('I_{\\Delta n} [mA]'), 'różnicowy prąd wyłączający'),
            Content(Math('t_{RCD} [ms]'), 'zmierzony czas wyłączenia RCD'),
            Content(Math('t_a [ms]'), 'wymagany czas wyłączenia RCD'),
            Content(Math('U_b [V]'), 'napięcie dotykowe zmierzone'),
            Content(Math('U_I [V]'), 'dopuszczalne napięcie dotykowe bezpiecznie'),
            Content(
                'Ocena: dopuszczalne napięcie dotykowe bezpiecznie ',
                Math('U_d <= U_I'), Math('t_{RCD} <= t_{A}'),
            ),
        )

    def get_columns(self):
        return (
            # MultiLine('Wyłącznik', 'RCD'),
            'Typ',
            MultiLine(Math('I_{\\Delta n}'), '[mA]'),
            MultiLine(Math('t_{a}'), '[ms]'), MultiLine(Math('t_{RCD}'), '[ms]'),
            MultiLine(Math('U_{b}'), '[V]'), MultiLine(Math('U_I'), '[V]'),
            'Ocena'
        )

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        RCDta = data['RCDta']
        return dict(
            rcd_model=RCDta['RCDTypeCombo'],
            In_mA=float(RCDta['deltaInCombo'][:-3]),
            ta=40e-3,
            trcd=float(RCDta['t_a.rawValue']),
            UI=float(RCDta['ul.rawValue']),
            UB=float(RCDta['ub.rawValue']),
            RE=float(RCDta['re.rawValue']),
        )

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        return (
            # row['rcd_model'],
            '[AC]',
            format_number(row['In_mA'], 0),
            format_number(row['ta'] * 1e3, 0), format_number(row['trcd'] * 1e3, 0),
            format_number(row['UB'], 1), format_number(row['UI'], 0),
            POZYTYWNA if (row['trcd'] <= row['ta'] and row['UB'] <= row['UI']) else NEGATYWNA,
        )


class RezystancjaIzolacji(MeasureDescriptor):
    title: str = 'Rezystancja izolacji zasilenia'
    measure_ids: Tuple[str, ...] = ('RisoUniSchuko',)

    def get_description(self) -> ContentItem:
        return (
            Content(Math('R_{LPE} [M\\Omega]'), 'Rezystancja między L a PE'),
            Content(Math('R_{LN} [M\\Omega]'), 'Rezystancja między L a N'),
            Content(Math('R_{a} [M\\Omega]'), 'Rezystancja wymagana'),
            Content(
                'Ocena: dopuszczalna rezystancja ',
                Math('R_{LPE} <= R_{a}'), Math('R_{LN} <= R_{a}'),
            ),
        )

    def get_columns(self):
        return (
            Math('R_{LPE} [M\\Omega]'),
            Math('R_{LN} [M\\Omega]'),
            Math('R_{a} [M\\Omega]'),
            'Ocena'
        )

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        RisoUniSchuko = data['RisoUniSchuko']
        return dict(
            R_LPE=float(RisoUniSchuko['R_LPE.rawValue']),
            R_LN=float(RisoUniSchuko['R_LN.rawValue']),
            R_a=250e6,
        )

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        return (
            format_number(row['R_LPE'] * 1e-6, 0, max_value=250),
            format_number(row['R_LN'] * 1e-6, 0, max_value=250),
            format_number(row['R_a'] * 1e-6, 0),
            POZYTYWNA if (row['R_LPE'] >= row['R_a'] and row['R_LN'] >= row['R_a']) else NEGATYWNA,
        )


class RezystancjaIzolacjiAll(MeasureDescriptor):
    title: str = 'Rezystancja izolacji zasilenia'
    measure_ids: Tuple[str, ...] = ()

    def get_description(self) -> ContentItem:
        return (
            Content(Math('R_{L1-L2} [G\\Omega]'), 'Rezystancja między L1 a L2'),
            Content(Math('R_{L2-L3} [G\\Omega]'), 'Rezystancja między L2 a L3'),
            Content(Math('R_{L3-L1} [G\\Omega]'), 'Rezystancja między L3 a L1'),
            Content(Math('R_{L1-N} [G\\Omega]'), 'Rezystancja między L1 a N'),
            Content(Math('R_{L2-N} [G\\Omega]'), 'Rezystancja między L2 a N'),
            Content(Math('R_{L3-N} [G\\Omega]'), 'Rezystancja między L3 a N'),
            Content(Math('R_{L1-PE} [G\\Omega]'), 'Rezystancja między L1 a PE'),
            Content(Math('R_{L2-PE} [G\\Omega]'), 'Rezystancja między L2 a PE'),
            Content(Math('R_{L3-PE} [G\\Omega]'), 'Rezystancja między L3 a PE'),
            Content(Math('R_{N-PE} [G\\Omega]'), 'Rezystancja między N a PE'),
            Content(Math('R_{a} [G\\Omega]'), 'Rezystancja wymagana'),
            Content(
                'Ocena: dopuszczalna rezystancja ',
                Math('R_{i} <= R_{a}'),
            ),
        )

    def get_columns(self):
        return (
            Math('R_{L1-L2} [G\\Omega]'),
            Math('R_{L2-L3} [G\\Omega]'),
            Math('R_{L3-L1} [G\\Omega]'),
            Math('R_{L1-N} [G\\Omega]'),
            Math('R_{L2-N} [G\\Omega]'),
            Math('R_{L3-N} [G\\Omega]'),
            Math('R_{L1-PE} [G\\Omega]'),
            Math('R_{L2-PE} [G\\Omega]'),
            Math('R_{L3-PE} [G\\Omega]'),
            Math('R_{N-PE} [G\\Omega]'),
            Math('R_{a} [G\\Omega]'),
            'Ocena'
        )

    def compute_row(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        return dict()

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        return (
            format_number(row['R_L1L2'] * 1e-9, 0, max_value=2),
            format_number(row['R_L2L3'] * 1e-9, 0, max_value=2),
            format_number(row['R_L3L1'] * 1e-9, 0, max_value=2),
            format_number(row['R_L1N'] * 1e-9, 0, max_value=2),
            format_number(row['R_L2N'] * 1e-9, 0, max_value=2),
            format_number(row['R_L3N'] * 1e-9, 0, max_value=2),
            format_number(row['R_L1PE'] * 1e-9, 0, max_value=2),
            format_number(row['R_L2PE'] * 1e-9, 0, max_value=2),
            format_number(row['R_L3PE'] * 1e-9, 0, max_value=2),
            format_number(row['R_NPE'] * 1e-9, 0, max_value=2),
            format_number(row['R_a'] * 1e-9, 0),
            POZYTYWNA if max(
                v for k, v in row.items() if k.startswith('R_')
            ) <= row['R_a'] else NEGATYWNA,
        )


class Uziemienie(MeasureDescriptor):
    title: str = 'Stan instalacji odgromowej i uziomów'

    def get_columns(self):
        return (
            Math('R_{S} [\\Omega]'),
            Math('R_{S\'} [\\Omega]'),
            Math('R_{a} [\\Omega]'),
            'Ciągłość',
            'Ocena'
        )

    def format_row(self, row: Dict[str, Any]) -> Tuple[ContentItem, ...]:
        return (
            format_number(row['R_S'], 1),
            format_number(row['R_SP'], 1),
            format_number(row['R_a'], 1),
            'Zachowana',
            POZYTYWNA,
        )
