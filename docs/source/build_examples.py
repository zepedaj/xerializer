#!/usr/bin/env python
import pprint
import climax as clx
import numpy as np
from xerializer import Serializer, Literal
from pglib.rentemp import RenTempFile
import sys
import json


@clx.command()
@clx.argument('outfile')
def main(outfile):
    serializer = Serializer()
    with RenTempFile(outfile, 'w', overwrite=True) as tmpf, open(tmpf.name, 'w') as fo:
        sys.stdout = fo

        # Print title
        doc_title = 'Examples'
        print('.. _Examples:\n')
        print(doc_title)
        print('='*len(doc_title))

        pp = pprint.PrettyPrinter()
        def my_print(x): return pprint.pformat(x, indent=2, sort_dicts=False)
        # my_print =lambda x: json.dumps(x, indent=2)

        # Print code block with examples
        print(*[
            '.. doctest::\n',
            ' :options: NORMALIZE_WHITESPACE\n\n'])

        [print('  '+x) for x in [
            '>>> from xerializer import Serializer, Literal',
            '>>> import numpy as np',
            '>>> srlzr = Serializer()',
            '\n']]

        for title, expr in [
                ('List of base types', "[1, 2.0, 'string']"),
                ('Dictionary', "{'key1': 'value1', 'key2':0}"),
                ('Dictionary with \'__type__\' field', "{'key1': 'value1', '__type__':0}"),
                # TODO: Document the from_serializable forms below. These should not go here,
                # this is not the best place for these as these examples require calling as_serializable.
                # ('Dictionary from nested lists', "{'__type__': 'dict', 'value':[['key0', 0], ['key1',1]]}"),
                # ('Dictionary from serialized keys', "{'__type__': 'dict', 'value': [[{'__type__':'tuple', 'value':[0,1]}, 0], ['key1',1]]}"),
                ('Classes', "dict"),
                ('Tuples', "(3, 1, 'string')"),
                ('Sets', "{3, 1, 'string'}"),
                ('Slices', "slice(10, 2, -2)"),
                ('Literals', "Literal([(1,2), {1:10, 1.0:'three', 'two':3}, 1.2])"),
                ('Numpy structured/shaped dtype', """
np.dtype([('id', 'i', (2,)),
          ('meta', [('name', 'U3'),
                    ('when', 'datetime64[D]')])])"""),
                ('Numpy array', "np.array([1,2,3])"),
                ('Datetime64 scalar', "np.datetime64('2020-10-10')"),
                ('Structured numpy array',
                 """
np.array([([1,2], ('abc', '2020-10-01')),
          ([10,20], ('def', '2020-10-11'))],
         dtype=[('id', 'i', (2,)),
                ('meta', [('name', 'U3'),
                          ('when', 'datetime64[D]')])])""")

        ]:
            expr_lns = expr.strip().split('\n')
            for _ln in (
                    [f'# {title}'] +
                    [f'>>> obj = {expr_lns[0]}'] +
                    [f'...       {_expr_ln}' for _expr_ln in expr_lns[1:]] +
                    [f'>>> srlzbl = srlzr.as_serializable(obj)', '>>> srlzbl'] +
                    # my_print(
                    # serializer.as_serializable(eval(' '.join(expr.split('\n')))),
                    # ).split('\n') +
                    [repr(serializer.as_serializable(eval(expr)))] +
                    [f'>>> srlzr.from_serializable(srlzbl)', repr(eval(expr))]):
                print(f'  {_ln}')
            print('')


if __name__ == '__main__':
    main()
