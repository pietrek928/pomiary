from contextlib import contextmanager
from typing import Union, Iterable, Tuple, Optional, List

from pydantic import BaseModel

ContentItem = Union[str, 'LatexObject', Tuple]


class Ctx:
    # TODO: text with escape ?
    def _print(self, s: str):
        print(s)

    def put(self, v: ContentItem):
        if isinstance(v, LatexObject):
            v.render(self)
        elif isinstance(v, (List, Tuple)):
            if v:
                for item in v[:-1]:
                    self.put(item).break_()
                self.put(v[-1])
        else:
            self._print(v)
        return self

    def break_(self):
        self._print('\\\\')
        return self

    def cmd(self, p, *args):
        args = ''.join(f'{{{a}}}' for a in args)
        self._print(f'\\{p}{args}')  # TODO: escape ?
        return self

    def usepackage(self, p):
        return self.cmd('usepackage', p)

    @contextmanager
    def begin(self, v, *args):
        self.cmd('begin', v, *args)
        yield
        self.cmd('end', v)


class CtxBuffer(Ctx):
    def __init__(self):
        self._txt = ''

    def _print(self, s: str):
        self._txt += s

    @property
    def value(self):
        return self._txt


class LatexObject(BaseModel):
    def render(self, ctx: Ctx):
        raise NotImplementedError('render not implemented')


class Document(LatexObject):
    document_class: str = 'article'
    header: Optional[ContentItem] = None
    title: str = ''
    author: str = ''
    date: str = '\\today'
    packages: Tuple[str, ...] = ()
    body: LatexObject = None

    def render(self, ctx: Ctx):
        ctx.cmd('documentclass', self.document_class)
        ctx.put('''
        \\usepackage[a4paper]{geometry}
        \\usepackage[T1]{fontenc}
        \\usepackage{polski}
        \\usepackage[utf8]{inputenc}
        \\usepackage[english, polish]{babel}
        ''')
        for p in self.packages:
            ctx.cmd('usepackage', p)
        if self.header is not None:
            ctx.put(self.header)
        if self.title:
            ctx.cmd('title', self.title)
        if self.author:
            ctx.cmd('author', self.author)
        if self.date:
            ctx.cmd('date', self.date)
        with ctx.begin('document'):
            # ctx.cmd('maketitle')
            if self.body is not None:
                self.body.render(ctx)


def _render_to_str(v: ContentItem) -> str:
    if isinstance(v, LatexObject):
        b = CtxBuffer()
        v.render(b)
        return b.value
    else:
        return str(v)


class HLine(LatexObject):
    def render(self, ctx: Ctx):
        ctx.put('\\noindent\\rule{\\textwidth}{1pt}')


class IncludeFile(LatexObject):
    fname: str

    def render(self, ctx: Ctx):
        ctx.cmd('include', self.fname).cmd('pagebreak')


class Content(LatexObject):
    items: Iterable[ContentItem] = ()

    def __init__(self, *items, **kwargs):
        super().__init__(items=tuple(items), **kwargs)

    def render(self, ctx: Ctx):
        for item in self.items:
            ctx.put(item)


class Center(Content):
    def render(self, ctx: Ctx):
        with ctx.begin('center'):
            super().render(ctx)


class DotList(LatexObject):
    items: Iterable[ContentItem] = ()

    def __init__(self, *items):
        super().__init__(items=tuple(items))

    def render(self, ctx: Ctx):
        with ctx.begin('itemize'):
            for item in self.items:
                ctx.cmd('item').put(item)


class ZeroSkipHeader(LatexObject):
    def render(self, ctx: Ctx):
        ctx.put('''
\\usepackage{etoolbox}
\\newcommand{\\zerodisplayskips}{%
  \\setlength{\\abovedisplayskip}{0pt}%
  \\setlength{\\belowdisplayskip}{0pt}%
  \\setlength{\\abovedisplayshortskip}{0pt}%
  \\setlength{\\belowdisplayshortskip}{0pt}}
\\appto{\\normalsize}{\\zerodisplayskips}
\\appto{\\small}{\\zerodisplayskips}
\\appto{\\footnotesize}{\\zerodisplayskips}
''')


class Box(Content):
    width: float = 1.

    def render(self, ctx: Ctx):
        ctx.put(f'\\parbox{{{self.width}\\textwidth}}{{')
        super().render(ctx)
        ctx.put('}')


class TextBox(Content):
    def render(self, ctx: Ctx):
        ctx.put('\\fbox{\\parbox{\\textwidth}{')
        super().render(ctx)
        ctx.put('}}')


class ItemContainer(LatexObject):
    i: ContentItem

    def __init__(self, i: ContentItem):
        super().__init__(i=i)

    def render(self, ctx: Ctx):
        ctx.put(self.i)


class Math(ItemContainer):
    def render(self, ctx: Ctx):
        ctx.put(f'${{{_render_to_str(self.i)}}}$')


class Bold(ItemContainer):
    def render(self, ctx: Ctx):
        ctx.put(f'\\textbf{{{_render_to_str(self.i)}}}')


class MultiLine(LatexObject):
    items: Tuple[ContentItem, ...]

    def __init__(self, *items):
        super().__init__(items=tuple(items))

    def render(self, ctx: Ctx):
        content = ''.join(
            f'\\hbox{{\\strut {_render_to_str(v)}}}'
            for v in self.items
        )
        ctx.put(f'\\vtop{{{content}}}')


class LongTable(LatexObject):
    caption: ContentItem = ''
    first_header: Optional[ContentItem] = None
    columns: Tuple[ContentItem, ...] = ()
    foot: ContentItem = Content('\\hline')
    last_foot: ContentItem = Content('\\hline')
    rows: Iterable[Tuple[ContentItem, ...]] = ()

    def _render_columns(self, ctx: Ctx):
        if self.columns:
            ctx.cmd('hline')
            ctx.put(self.columns[0])
            # ctx.cmd('multicolumn', '1', '|c|', _render_to_str(self.columns[0]))
            for col in self.columns[1:]:
                ctx.put(' & ')
                ctx.put(col)
                # ctx.cmd('multicolumn', '1', 'c|', _render_to_str(col))
            ctx.break_()
            ctx.cmd('hline')

    def _render_row(self, ctx: Ctx, row: Tuple[ContentItem, ...]):
        ctx.put(row[0])
        for item in row[1:]:
            ctx.put(' & ')
            ctx.put(item)
        ctx.break_()

    def render(self, ctx: Ctx):
        col_descr = '|'.join('l' for l in self.columns)
        with ctx.begin('longtable', f'|{col_descr}|'):
            ctx.cmd('caption', _render_to_str(self.caption))
            # ctx.cmd('label', 'tab:long')
            ctx.break_()

            if self.first_header is not None:
                ctx.put(self.first_header)
            self._render_columns(ctx)
            ctx.cmd('endfirsthead')

            self._render_columns(ctx)
            ctx.cmd('endhead')

            ctx.put(self.foot)
            ctx.cmd('endfoot')
            ctx.put(self.last_foot)
            ctx.cmd('endlastfoot')

            for row in self.rows:
                self._render_row(ctx, row)


class Attachment(Content):
    name: ContentItem = '.'

    def render(self, ctx: Ctx):
        ctx.put('Załącznik: ').put(self.name).put('\\hfill').put(HLine())
        super().render(ctx)
        ctx.cmd('pagebreak')


class MeasurePageSetup(LatexObject):
    ce_data: str = '02/2022'

    firma: ContentItem = '.'
    data_pomiarow: ContentItem = '.'
    wykonawca: ContentItem = '.'
    miejsce: ContentItem = '.'

    def _head(self):
        return Content(
            '\\footnotesize ',
            f'CE 1/{self.ce_data}/Ur \\hfill ',
            'Data pomiarów: ', self.data_pomiarow, ' \\newline ',
            'Wykonawca pomiarów: ', self.wykonawca, ' \\hfill\\newline ',
            'Miejsce przeprowadzenia pomiarów: ', self.miejsce, '\\hfill ',
        )

    def _foot(self):
        return Content(self.firma, f'\\hfill CE 1/{self.ce_data}/Ur\\quad\\thepage/\\pageref{{LastPage}}')

    def render(self, ctx: Ctx):
        ctx.usepackage('lastpage') \
            .usepackage('fancyhdr') \
            .cmd('pagestyle', 'fancy') \
            .cmd('fancyhf', '') \
            .cmd('fancyhead[CO]', _render_to_str(self._head())) \
            .cmd('rfoot', _render_to_str(self._foot())) \
            .put('\\fancypagestyle{FancyTitle}{\\renewcommand{\\headrulewidth}{0pt}\\fancyhead{}}')


class MeasureTitlePage(LatexObject):
    ce_data: str = '02/2022'

    firma: ContentItem = '.'
    data_pomiarow: ContentItem = '.'
    wykonawca: ContentItem = '.'
    miejsce: ContentItem = '.'
    pomiarowcy: ContentItem = '.'

    def render(self, ctx: Ctx):
        ctx.cmd('thispagestyle', 'FancyTitle') \
            .put(Content(
            Center(
                '\\includesvg[width=0.4\\columnwidth]{img/measure-icon.svg}'
            ),
            Center(
                HLine(), self.firma
            ),
            Center('\\Huge\\textbf{Protokół z pomiarów ochronnych}'),
            Center(f'\\Large CE 1/{self.ce_data}/Ur'),
        )).put(
            '\\vfill\\flushleft'
        ).put(
            HLine()
        ).put('Miejsce przeprowadzenia pomiarów:').break_() \
            .put(self.miejsce).break_() \
            .put('Data pomiarów:').break_() \
            .put(self.data_pomiarow).break_() \
            .put('Wykonawca pomiarów:').break_() \
            .put(self.wykonawca).break_() \
            .put('Pomiarowcy:').break_() \
            .put(self.pomiarowcy).break_()


class MeasureDescriptionPage(LatexObject):
    ce_data: str = '02/2022'
    wykonawca: ContentItem = ('.', '.', '.', '.')
    zleceniodawca: ContentItem = ('.', '.', '.', '.')
    miejsce: ContentItem = ('.', '.', '.', '.')
    orzeczenie: ContentItem = ('.', '.', '.', '.')

    rodzaj_pomiarow: ContentItem = '.'
    data_pomiarow: ContentItem = '.'
    instalacja: ContentItem = '.'
    pogoda: ContentItem = '.'
    data_nastepnych_pomiarow: ContentItem = '.'

    def render(self, ctx: Ctx):
        ctx.cmd('pagebreak').cmd('thispagestyle', 'FancyTitle') \
            .put(Content(
            '\\hfill',
            '\\includesvg[width=0.15\\columnwidth]{img/measure-icon.svg}',
            Box((Bold('Wykonawca pomiarów:'), self.wykonawca), width=.4),
        )).put('\\quad\\\\\\quad\\\\\\quad\\\\\\quad\\\\').put(
            Center('\\Large Protokół z pomiarów ochronnych')
        ).put(
            Center(Bold(f'\\Large CE 1/{self.ce_data}/Ur'))
        ).put('\\vfill').put(TextBox(
            (Bold('Zleceniodawca:'), self.zleceniodawca)
        )).put(TextBox(
            (Bold('Miejsce przeprowadzenia pomiarów:'), self.miejsce)
        )).put(TextBox(
            Box((
                Content(Bold('Rodzaj pomiarów:'), self.rodzaj_pomiarow),
                Content(Bold('Data pomiarów:'), self.data_pomiarow),
                Content(Bold('Instalacja:'), self.instalacja),
            ), width=.5),
            Box(
                (Content(Bold('Pogoda:'), self.pogoda),
                 Content(Bold('Data następnych pomiarów:'), self.data_nastepnych_pomiarow), '\\quad'),
                width=.5
            )
        )).put(TextBox(
            (Bold('Orzeczenie:'), self.orzeczenie)
        )).cmd('pagebreak')
