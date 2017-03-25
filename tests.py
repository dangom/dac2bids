import unittest

from nose.tools import raises

from refactored import *


class Dac2BidsTests(unittest.TestCase):

    @raises(NotADirectoryError)
    def test_inexistent_input_dir(self):
        input_dir="blabasfjdhkjshdf"
        output_dir="ulalala"
        Dac2Bids(input_dir, output_dir)


class BidifyerTests(unittest.TestCase):

    def test_default_input(self):
        bids = Bidifyer()
        self.assertEqual(bids.tag, "sub-01")

    def test_formatter(self):
        bids = Bidifyer(format_precision=5)
        self.assertEqual(bids.tag, "sub-00001")

    def test_subject_tag(self):
        config = {"subject_number": 3, "subject_label": "control"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.subject_tag, "sub-control03")
        self.assertEqual(bids.tag, "sub-control03")

    def test_session_tag(self):
        config = {"session_number": 8, "session_label": "pre"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.session_tag, "ses-pre08")
        self.assertEqual(bids.tag, "sub-01_ses-pre08")

    def test_session_tag_no_number(self):
        config = {"session_label": "pre"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.session_tag, "ses-pre")
        self.assertEqual(bids.tag, "sub-01_ses-pre")

    def test_subject_session_tag(self):
        config = {"subject_number": 3, "subject_label": "control",
                  "session_number": 8, "session_label": "pre"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.session_tag, "ses-pre08")
        self.assertEqual(bids.tag, "sub-control03_ses-pre08")

    def test_acquisition_tag(self):
        # No such thing as acquisition number. (But could maybe be used for ME?!)
        config = {"acquisition_number": 3, "acquisition_label": "sb"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.acquisition_tag, "acq-sb03")
        self.assertEqual(bids.tag, "sub-01_acq-sb03")

    def test_acquisition_tag_label_only(self):
        # No such thing as acquisition number. (But could maybe be used for ME?!)
        config = {"acquisition_label": "test"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.acquisition_tag, "acq-test")
        self.assertEqual(bids.tag, "sub-01_acq-test")

    def test_acquisition_tag_number_only(self):
        # No such thing as acquisition number. (But could maybe be used for ME?!)
        config = {"acquisition_number": 3}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.acquisition_tag, "acq-03")
        self.assertEqual(bids.tag, "sub-01_acq-03")

    def test_pe_direction_tag(self):
        config = {"pe_direction_label": "reverse"}
        bids = Bidifyer(bids_config=config)
        self.assertEqual(bids.pe_direction_tag, "dir-reverse")
        self.assertEqual(bids.tag, "sub-01_dir-reverse")

    def test_all_order(self):
        test_configuration = {"subject_number": 1, # mandatory
                              "subject_label": "sublabel", # optional
                              "session_number": 3, # optional
                              "session_label": "seslabel", # optional
                              "task_label": "tasklabel", # mandatory for functional data
                              "acquisition_number": 5, # for Multiecho
                              "acquisition_label": "acqlabel", # optional
                              "pe_direction_label": "dirlabel", # optional
                              "run_index": 8} # optional

        bids = Bidifyer(bids_config=test_configuration, format_precision=3)
        self.assertEqual(bids.tag, "sub-sublabel001_ses-seslabel003_task-tasklabel_acq-acqlabel05_dir-dirlabel_run-08")

    def malformed_label_error(self):
        config = {"pe_direction_label": "reverse/"}
        self.assertRaises(BidsMalformedLabelError, Bidifyer(bids_config=config))

    def missing_mandatory_error(self):
        config = {"subject_number": None}
        self.assertRaises(BidsInconsistentNamingError, Bidifyer(bids_config=config))
