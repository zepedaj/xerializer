from xerializer import utils as mdl
import pickle
from xerializer import serializable
from dataclasses import dataclass
from jztools.parallelization.threading.queue import put_loop, get_loop
from multiprocessing import Queue, Event, Process
from concurrent.futures import ProcessPoolExecutor

from unittest import TestCase


@serializable
@dataclass
class MyClass:
    a: int
    b: int

    def __iter__(self):
        yield from range(5)


def worker_with_queue(obj, q, exit_events):
    if q is not None:
        try:
            put_loop(q, (obj, type(obj)), exit_events)
        except BaseException as err:
            put_loop(q, err, exit_events)

    return obj, type(obj)


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

    def test_pool(self):

        with ProcessPoolExecutor() as pool:
            future = pool.submit(
                worker_with_queue, mdl.AsPickleable(mc := MyClass(1, 2)), None, {}
            )

        obj, cls = future.result()
        self.assertIs(cls, MyClass)
        self.assertEqual(obj, mc)


class TestAsProcessParam(TestCase):
    def test_process(self):

        q = Queue(1)
        exit_events = {"exit": Event()}

        p = Process(
            target=worker_with_queue,
            args=(mdl.AsProcessParam(mc := MyClass(1, 2)), q, exit_events),
        )

        p.start()
        try:
            obj, cls = get_loop(q, exit_events)
            self.assertIs(cls, MyClass)
            self.assertEqual(obj, mc)
        except BaseException:
            exit_events["exit"].set()
            raise
        finally:
            p.join()
