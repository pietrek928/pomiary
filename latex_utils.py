from contextlib import contextmanager
from typing import Union, Iterable, Tuple, Optional

from pydantic import BaseModel

ContentItem = Union[str, 'LatexObject']


class Ctx:
    # TODO: text with escape ?
    def _print(self, s: str):
        print(s)

    def put(self, v: ContentItem):
        if isinstance(v, LatexObject):
            v.render(self)
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


class Content(LatexObject):
    items: Iterable[ContentItem] = ()

    def __init__(self, *items):
        super().__init__(items=tuple(items))

    def render(self, ctx: Ctx):
        for item in self.items:
            ctx.put(item)


class Center(Content):
    def render(self, ctx: Ctx):
        with ctx.begin('center'):
            super().render(ctx)


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


class TextBox(Content):
    def render(self, ctx: Ctx):
        ctx.put('\\fbox{\\parbox{\\textwidth}{')
        super().render(ctx)
        ctx.put('}}')


class Math(LatexObject):
    t: ContentItem

    def __init__(self, t: ContentItem):
        super().__init__(t=t)

    def render(self, ctx: Ctx):
        ctx.put(f'${{{_render_to_str(self.t)}}}$')


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


class MeasurePageSetup(LatexObject):
    def _head(self):
        return '''
\\footnotesize
CE 1/09/2021/Ur \\hfill Data pomiarów: \\newline
Wykonawca pomiarów \\hfill \\quad \\newline
Miejsce przeprowadzenia pomiarów: \\hfill
        '''

    def _foot(self):
        return 'CE 1/09/2021/Ur\\quad\\thepage/\\pageref{LastPage}'

    def render(self, ctx: Ctx):
        ctx.usepackage('lastpage') \
            .usepackage('fancyhdr') \
            .cmd('pagestyle', 'fancy') \
            .cmd('fancyhf', '') \
            .cmd('fancyhead[CO]', self._head()) \
            .cmd('rfoot', self._foot())
