from xerializer import utils as mdl
import pickle
from xerializer import serializable
from dataclasses import dataclass

from unittest import TestCase


@serializable
@dataclass
class MyClass:
    a: int
    b: int


class TestAsPickleable(TestCase):

    def test_all(self):
        mc = MyClass(1, 2)
        mc_as = mdl.AsPickleable(mc)
        self.assertIsInstance(mc_as.__reduce__(), tuple)
        pckld = pickle.dumps(mc_as)
        pckld_reduce = pickle.dumps(mdl.AsPickleable(mc).__reduce__())
        k = 3  # Not sure why 3 works...
        self.assertEqual(pckld[:-k], pckld_reduce[:-k])
        self.assertEqual(mc, pickle.loads(pickle.dumps(mdl.AsPickleable(mc))))

    # def test_pickle_serializer(self):
    #     from xerializer import Serializer
    #     import pickle

    #     srlzr = Serializer()
    #     pickle.dumps(srlzr)
