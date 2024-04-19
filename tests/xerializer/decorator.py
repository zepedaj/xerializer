from xerializer import decorator as mdl, Serializer
from jztools.py import entity_name
from xerializer.serializer import UnserializableType
from unittest import TestCase


class TestDecorator(TestCase):
    def test_objects(self):

        # DEFINE SEVERAL @serializable-decorated classes.
        class _T:
            def __eq__(self, b):
                return type(self) == type(b) and all(
                    (
                        vars(self)[key] == vars(b)[key]
                        for key in vars(self)
                        if key != "_xerializable_params"
                    )
                )

        @mdl.serializable(signature="A", explicit_defaults=False)
        class A(_T):
            def __init__(self, a, b, *args, c=100, d=200, **kwargs):
                self.a = a
                self.b = b
                self.args = args
                self.c = c
                self.d = d
                self.kwargs = kwargs

        @mdl.serializable(signature="B")
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

        # Check signatures
        self.assertEqual(srlzr.get_signature(A), "A")
        self.assertEqual(
            srlzr.get_signature(C),
            "tests.xerializer.decorator:TestDecorator.test_objects.<locals>.C",
        )

        # Test compactness of representation
        # ########################################
        self.assertEqual(
            srlzr.as_serializable(A(1, 2, 3, c=3)),
            {"__type__": "A", "a": 1, "b": 2, "args": [3], "c": 3},
        )
        self.assertEqual(srlzr.as_serializable(B()), {"__type__": "B"})
        self.assertEqual(
            srlzr.as_serializable(B(1, 2, 3)), {"__type__": "B", "args": [1, 2, 3]}
        )
        self.assertEqual(
            srlzr.as_serializable(B(a=1, b=2, c=3)),
            {"__type__": "B", "a": 1, "b": 2, "c": 3},
        )
        # Test case when 'args' name crashes with a keyword -- auto.
        self.assertEqual(
            srlzr.as_serializable(A(1, 2, 3, c=3, args=5, x=6, y=7)),
            {
                "__type__": "A",
                "a": 1,
                "b": 2,
                "c": 3,
                "args": [3],
                "kwargs": {"args": 5, "x": 6, "y": 7},
            },
        )
        # Test same without crashes -- auto.
        self.assertEqual(
            srlzr.as_serializable(A(1, 2, 3, c=3, z=5, x=6, y=7)),
            {
                "__type__": "A",
                "a": 1,
                "b": 2,
                "c": 3,
                "args": [3],
                "z": 5,
                "x": 6,
                "y": 7,
                "z": 5,
            },
        )

        # Test equivalence of serialized / deserialized classes.
        ############################################################
        for obj in [
            A(0, 1),
            A(0, 1, e="500"),
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

    def test_callables(self):

        ##########
        @mdl.serializable()
        def fxn1(a, b):
            return (a, b)

        @mdl.serializable()
        def fxn2(*args, **kwargs):
            return args, kwargs

        @mdl.serializable()
        def fxn3(a, b, *args, c=1, d=2, **kwargs):
            return a, b, args, c, d, kwargs

        @mdl.serializable()
        class A:
            def __init__(self, a, b):
                self.a = a
                self.b = b

            def __eq__(self, v):
                return self.a == v.a and self.b == v.b

            # @mdl.serializable()
            # def im1(self, a, b):
            #     return (self, a, b)

            # @mdl.serializable()
            # @classmethod
            # def cm1(cls, a, b):
            #     return (a, b)

            # @mdl.serializable()
            # def im2(self, *args, **kwargs):
            #     return self, args, kwargs

            # @mdl.serializable()
            # @classmethod
            # def cm2(cls, *args, **kwargs):
            #     return args, kwargs

            @mdl.serializable()
            def im3(self, a, b, *args, c=1, d=2, **kwargs):
                return self, a, b, args, c, d, kwargs

            @mdl.serializable()
            @classmethod
            def cm3(cls, a, b, *args, c=1, d=2, **kwargs):
                return cls, a, b, args, c, d, kwargs

            @mdl.serializable()
            @staticmethod
            def sm3(a, b, *args, c=1, d=2, **kwargs):
                return a, b, args, c, d, kwargs

        ###########
        serializer = Serializer()

        # Check signatures
        self.assertEqual(
            serializer.get_signature(A.im3),
            "tests.xerializer.decorator:TestDecorator.test_callables.<locals>.A.im3",
        )

        for val, srlzbl in [
            (fxn1(1, 2), {"__type__": entity_name(fxn1), "a": 1, "b": 2}),
            #
            (fxn2(1, 2), {"__type__": entity_name(fxn2), "args": [1, 2]}),
            #
            (fxn2(1, 2, c=3), {"__type__": entity_name(fxn2), "args": [1, 2], "c": 3}),
            #
            (
                fxn2(1, 2, kwargs=3),
                {
                    "__type__": entity_name(fxn2),
                    "args": [1, 2],
                    "kwargs": {"kwargs": 3},
                },
            ),
            #
            (
                fxn3(1, 2, 3, c=4, d=5, e=6),
                {
                    "__type__": entity_name(fxn3),
                    "a": 1,
                    "b": 2,
                    "args": [3],
                    "c": 4,
                    "d": 5,
                    "e": 6,
                },
            ),
            #
            # For instance methods to work, from_serializable should take kwargs instead of **kwargs -- otherwise 'self' gets passed twice.
            # (A(10, 20).im1(1, 2),
            #  {'__type__': entity_name(A.im1),
            #   'self': serializer.as_serializable(A(10, 20)), 'a': 1, 'b': 2}),
            #
            (
                A.cm3(1, 2, 3, c=4, d=5, e=6),
                {
                    "__type__": entity_name(A.cm3),
                    "a": 1,
                    "b": 2,
                    "args": [3],
                    "c": 4,
                    "d": 5,
                    "e": 6,
                },
            ),
            #
            (
                A.sm3(1, 2, 3, c=4, d=5, e=6),
                {
                    "__type__": entity_name(A.sm3),
                    "a": 1,
                    "b": 2,
                    "args": [3],
                    "c": 4,
                    "d": 5,
                    "e": 6,
                },
            ),
        ]:
            self.assertEqual(val, serializer.from_serializable(srlzbl))

    def test_inheritance(self):
        @mdl.serializable()
        class A:
            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

            def __eq__(self, x):
                vars0 = {_key: _val for _key, _val in vars(x).items() if _key[0] != "_"}
                vars1 = {
                    _key: _val for _key, _val in vars(self).items() if _key[0] != "_"
                }
                return vars0 == vars1

        @mdl.serializable()
        class B(A):
            def __init__(self, d, e, f, *args, **kwargs):
                self.d = d
                self.e = e
                self.f = f
                super().__init__(*args, **kwargs)

        srlzr = Serializer()
        obj_b = B(4, 5, 6, 1, 2, 3)

        self.assertEqual(srlzr.deserialize(srlzr.serialize(obj_b)), obj_b)
