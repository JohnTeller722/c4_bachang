import unittest
from app.models.experiment import Experiment

class ExpTestCase(unittest.TestCase):

    def test_experiment_init(self):
        a = Experiment("test1")
        assert a.expUUID
        assert a.name == "test1"

