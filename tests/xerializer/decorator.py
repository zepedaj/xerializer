from xerializer import decorator as mdl, Serializer
from xerializer.serializer import UnserializableType
from unittest import TestCase


class TestDecorator(TestCase):

    def test_all(self):

        # DEFINE SEVERAL @serializable-decorated classes.
        class _T:
            def __eq__(self, b):
                return type(self) == type(b) and all(
                    (vars(self)[key] == vars(b)[key] for key in vars(self)
                     if key != '_xerializable_params'))

        @mdl.serializable(signature='A', explicit_defaults=False)
        class A(_T):
            def __init__(self, a, b, *args, c=100, d=200, **kwargs):
                self.a = a
                self.b = b
                self.args = args
                self.c = c
                self.d = d
                self.kwargs = kwargs

        @mdl.serializable(signature='B')
        class B(_T):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        @mdl.serializable()
        class C(_T):
            def __init__(self, a, b, c=100, d=200):
                self.a = a
                self.b = b
                self.c = c
                self.d = d

        @mdl.serializable()
        class D(_T):
            def __init__(self, a=10, b=20, c=100, d=200):
                self.a = a
                self.b = b
                self.c = c
                self.d = d

        class Dchild(D):
            pass

        @mdl.serializable()
        class Dchild2(D):
            pass

        class Dchild3(D):
            pass

        Dchild3 = mdl.serializable()(Dchild3)

        class E(_T):
            def __init__(self, a=10, b=20, c=100, d=200):
                self.a = a
                self.b = b
                self.c = c
                self.d = d

        E = mdl.serializable()(E)

        @mdl.serializable()
        class F(_T):
            pass

        srlzr = Serializer()

        # Test compactness of representation
        # ########################################
        self.assertEqual(srlzr.as_serializable(A(1, 2, 3, c=3)),
                         {'__type__': 'A', 'a': 1, 'b': 2, 'args': [3], 'c': 3})
        self.assertEqual(srlzr.as_serializable(B()),
                         {'__type__': 'B'})
        self.assertEqual(srlzr.as_serializable(B(1, 2, 3)),
                         {'__type__': 'B', 'args': [1, 2, 3]})
        self.assertEqual(srlzr.as_serializable(B(a=1, b=2, c=3)),
                         {'__type__': 'B', 'a': 1, 'b': 2, 'c': 3})
        # Test case when 'args' name crashes with a keyword -- auto.
        self.assertEqual(srlzr.as_serializable(A(1, 2, 3, c=3, args=5, x=6, y=7)), {
                         '__type__': 'A', 'a': 1, 'b': 2, 'c': 3, 'args': [3],
                         'kwargs': {'args': 5, 'x': 6, 'y': 7}})
        # Test same without crashes -- auto.
        self.assertEqual(srlzr.as_serializable(A(1, 2, 3, c=3, z=5, x=6, y=7)), {
                         '__type__': 'A', 'a': 1, 'b': 2, 'c': 3, 'args': [3],
                         'z': 5, 'x': 6, 'y': 7, 'z': 5})

        # Test equivalence of serialized / deserialized classes.
        ############################################################
        for obj in [
                A(0, 1),
                A(0, 1, e='500'),
                A(0, 1, 2, 3, 4, c=300, d=400),
                B(0, 1, 2, 3),
                B(x=4, y=5, z=6),
                B(0, 1, 2, 3, x=4, y=5, z=6),
                C(0, 1),
                C(0, 1, 2, 3),
                C(0, 1, d=10),
                D(),
                D(1, 2, 3, 4),
                D(d=5),
                D(a=5),
                D(a=5, b=6, c=7, d=8),
                E(a=5, b=6, c=7, d=8),
                Dchild2(a=5, b=6, c=7, d=8),
                Dchild3(a=5, b=6, c=7, d=8),
                F(),
        ]:
            dsrlzd_obj = srlzr.deserialize(srlzr.serialize(obj))
            # print(vars(obj), vars(dsrlzd_obj))
            self.assertEqual(dsrlzd_obj, obj)

        with self.assertRaises(UnserializableType):
            srlzr.serialize(Dchild())