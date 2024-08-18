import unittest
from app.models.experiment import Experiment

class ExpTestCase(unittest.TestCase):

    def test_experiment_init(self):
        a = Experiment("test1")
        assert a.expUUID
        assert a.name == "test1"

    def test_experiment_load(self):
        a = Experiment("test1")
        a.from_yaml(yml_file="test/resource/range-config.yaml")
        assert a.expUUID == "52129324-81d7-4e05-83c2-fc39dd456984"
        assert 0

