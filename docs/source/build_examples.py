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
        #my_print =lambda x: json.dumps(x, indent=2)

        # Print code block with examples
        print('.. code-block::\n\n')
        for title, expr in [
                ('List of base types', "[1, 2.0, 'string']"),
                ('Dictionary', "{'key1': 'value1', 'key2':0}"),
                ('Dictionary with \'__type__\' field', "{'key1': 'value1', '__type__':0}"),
                ('Tuples', "(1,'string',3)"),
                ('Sets', "{1,'string',3}"),
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
            for _ln in (
                    [f'# {title}'] +
                    [f'# {_expr_ln}' for _expr_ln in expr.split('\n')] +
                    my_print(
                    serializer.as_serializable(eval(' '.join(expr.split('\n')))),
                    ).split('\n')):
                print(f'  {_ln}')
            print('')


if __name__ == '__main__':
    main()
