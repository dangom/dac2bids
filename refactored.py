# Time-stamp: <2017-03-24 12:03:34 danielpgomez>
"""
Dac2Bids generates a YAML configuration file for dcm2niibatch
from a root folder with subfolders of DICOM files.

Dac2Bids contains three main units of logic:

1. DicomParser
Identify what kind of scan is contained within a folder.

2. Bidifyer
Compose a BIDS compliant name from data in a folder.

3. BidsExporter
Convert the BIDS compliant name and the directory and output
into a YAML file.
"""
import os


class UnproperDicomSortingError(Exception):
    """
    Raised if a given directory contains multiple nested
    folders with DICOMs.
    """
    pass

class BidsInconsistentNamingError(Exception):
    """
    Raised when an obligatory BIDS label is missing.
    """


class Dac2Bids:
    """
    Orchestrate the production of a dcm2niix (dcm2niibatch)
    compatible YAML file.
    """

    def __init__(self, input_dir, output_dir,
                 ignore_dirs=None, skip_incomplete=False,
                 subject_number=None, session_number=None):
        """
        Parse configuration and verify inputs.

        :param input_dir: Toplevel directory to run Dac2Bids
        :param output_dir: Target output directory for BIDS NIfTIs.
        :param ignore_dirs: File or list of directories to ignore
        :param skip_incomplete: Skip series with incomplete volumes.
        :param subject_number: Subject number. If None, guess from input_dir.
        :param session_number: session number. If None, guess from output_dir.
        :returns: None
        :rtype: None

        """

        if not os.path.isdir(input_dir):
            error_msg = "%s doesn't exist or is not a directory" % input_dir
            raise NotADirectoryError(error_msg)

        self.input_dir = input_dir

        self.directory_list = dict.fromkeys(lsdirs(self.input_dir))
        for d in self.directory_list:
            if has_subdirectory(d):
                error_msg = "Directory %s contains subdirectories" % d
                raise UnproperDicomSortingError(error_msg)

        self.ignore_dirs = ignore_dirs
        self.skip_incomplete = skip_incomplete

    def dispatch_parsers(self):
        """
        Iterate over self.directory_list, guess type of acquisition and
        dispatch a corresponding Parser worker to produce a filename.

        :returns: None
        :rtype: None
        """




class DicomParser:
    """
    Contains all logic and heuristics to decide whether a folder contains
    anatomical, diffusion, functional or physiological data (or field maps).
    """
    def __init__(self, input_file=None):
        self.input_file = input_file

    @property
    def img_type(self):
        print("img_type")

    @property
    def seqname(self):
        pass

    @property
    def repetitions(self):
        pass

    @property
    def contrasts(self):
        pass

class Bidifyer:
    """
    Provide functionality to compose a BIDS compliant filename.
    This class is a clone of the BIDS spec directly.
    """
    bids_version = "1.0.1"

    canonical_field = { "subject" : "sub",
                        "session" : "ses",
                        "acquisition" : "acq",
                        "run" : "run",
    }

    def __init__(self,
                 subject_number, subject_label=None,
                 session_number=None, session_label=None, format_precision=2,
                 task_label=None, acquisition_label=None, run_index=None):
        """

        :param subject_number: Subject number, required.
        :param subject_label: A label to come before the number, e.g. "control".
        :param session_number: Session number
        :param session_label: Label to come before the session, e.g. "pre"
        :param format_precision: Zeropadding of subject and session numbers.
        :param acquisition_label: Acquisition identifyer, e.g. "singleband
        :param run_index: Run index
        :returns: None
        :rtype: None

        """
        self.subject_number = subject_number
        self.subject_label = subject_label
        self.session_number = session_number
        self.session_label = session_label
        self.task_label = task_label
        self.acquisition_label = acquisition_label
        self.run_index = run_index
        self.format_precision = format_precision
        # A string to account for sub-N, sub-0N or sub-00N.
        self.formatter = "{" + ":0{}d".format(format_precision) + "}"


    def subject_tag(self):
        """
        Generate subject tag according to the BIDS specification.

        :returns: Subject tag
        :rtype: String

        """
        label = self.subject_label if self.subject_label is not None else ""
        number = self.formatter.format(self.subject_number)
        tag = "{0}-{1}{2}".format(self.canonical_field["subject"],
                                  label,
                                  number)
        return tag

    def session_tag(self):
        """
        Generate session tag according to the BIDS specification.

        :returns: Session tag
        :rtype: String

        """
        label = self.session_label if self.session_label is not None else ""
        if self.session_number is not None:
            number = self.formatter.format(self.session_number)
        else:
            number = ""

        tag = "{0}-{1}{2}".format(self.canonical_field["session"],
                                  label,
                                  number)
        return tag


class AnatomicalBidifyer(Bidifyer):

    def __init__(self, *args, **kwargs):
        super().__init__(self *args, **kwargs)

class FunctionalBidifyer(Bidifyer):

    def __init__(self, *args, **kwargs):
        super().__init__(self *args, **kwargs)
        if self.task_label is None:
            error_msg = "Functional Data require a proper task label."
            raise BidsInconsistentNamingError(error_msg)


class PhysiologicalBidifyer(Bidifyer):
    def __init__(self):
        pass


class DiffusionBidifyer(Bidifyer):
    def __init__(self):
        pass


# SOME HELPER FUNCTIONS
def lsdirs(folder):
    """
    List all directories in a folder. Ignore files.
    """
    return filter(lambda x:
                  os.path.isdir(os.path.join(folder, x)),
                  os.listdir(folder))

def has_subdirectory(folder):
    """
    Return true if a folder has a subdirectory.
    Ignore hidden directories (such as .git, for example)
    """
    for root, subdirs, files in os.walk(folder):
        if subdirs and not all(d[0]=='.' for d in subdirs):
            return True
        else:
            return False
