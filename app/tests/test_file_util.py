import unittest
from common import file_util
import datetime

class Test_file_util(unittest.TestCase):

    def test_parse_annotated(self):
        result=file_util.create_file_record("/records/./annot_repo/IG/001-020/IG001.eaf",datetime.datetime.now(), "B1")
        self.assertEqual("IG", result.annotator)
        self.assertEqual("001-020", result.listnumm)
        self.assertIsNotNone(result.record_path)


    def test_parse_org(self):
        result=file_util.create_file_record("/records/./org_repo/GD/1/res/GD001.eaf",datetime.datetime.now(), "B1")
        self.assertEqual("GD", result.annotator)
        self.assertEqual("1/res", result.listnumm)
        self.assertIsNotNone(result.record_path)


    def test_parse_org_wo_listnum(self):
        result=file_util.create_file_record("/records/./org_repo/ST/res/ST001.eaf",datetime.datetime.now(), "B1")
        self.assertEqual("ST", result.annotator)
        self.assertEqual("res", result.listnumm)
        self.assertIsNotNone(result.record_path)


    def test_parse_wrong(self):
        result=file_util.create_file_record("wrong/ST001.eaf",datetime.datetime.now(), "B1")
        self.assertIsNone(result.annotator)
        self.assertIsNone(result.listnumm)
        self.assertIsNotNone(result.record_path)
        self.assertEqual( file_util.ERR_FILE_FORMAT, result.error_code)


    def test_file_name(self):
        file_name=file_util.get_file_name("/records/./org_repo/ST/res/ST001.eaf")
        self.assertEqual("ST001.eaf", file_name)
