# Time-stamp: <2017-03-24 19:33:56 danielpgomez>
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
import functools
import os
import string


# SOME HELPER FUNCTIONS
def lsdirs(folder):
    """
    Return an iterable for all directories in a folder.
    Ignore files.
    """
    return filter(lambda x:
                  os.path.isdir(os.path.join(folder, x)),
                  os.listdir(folder))

def has_subdirectory(folder):
    """
    Return true if a folder has a subdirectory.
    Ignore hidden directories (such as .git, for example)
    """
    # root, subdirs, files
    for _, subdirs, _ in os.walk(folder):
        return subdirs and not all(d[0] == '.' for d in subdirs)

def formatter(precision=2):
    """
    Formatter returns a formatting function for a given precision.
    Ex. f =formatter(2) => f(3) = '03'
    Ex. f =formatter(5) => f(3) = '00003'

    :param precision: number of digits for formatter
    :returns: a lambda function that formats text.
    :rtype: function

    """
    form = "{" + ":0{}d".format(precision) + "}"
    return lambda x: form.format(x)

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
    pass

class BidsMalformedLabelError(Exception):
    """
    Raised when a Bids label contains symbols.
    """
    pass


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
            error_msg = "\"%s\" doesn't exist or is not a directory" % input_dir
            raise NotADirectoryError(error_msg)

        self.input_dir = input_dir
        self.output_dir = output_dir

        self.directory_list = dict.fromkeys(lsdirs(self.input_dir))
        for dicomdir in self.directory_list:
            if has_subdirectory(dicomdir):
                error_msg = "Directory %s contains subdirectories" % dicomdir
                raise UnproperDicomSortingError(error_msg)

        self.ignore_dirs = ignore_dirs
        self.skip_incomplete = skip_incomplete

        # FIXME Add automatic checks to read subject and session numbers
        # from the input directory, if subject and session numbers are None.
        self.config["subject_number"] = subject_number
        self.config["session_number"] = session_number


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
    This class clones the BIDS spec directly.
    """
    bids_version = "1.0.1"

    bids_abbreviations = {"subject" :"sub",
                          "session" :"ses",
                          "task" :"task",
                          "acquisition" :"acq",
                          "pe_direction": "dir", # Phase encoding, for TOPUP.
                          "run" :"run"}

    bids_tag_separator = "_"

    default_configuration = {"subject_number": 1, # mandatory
                             "subject_label": "", # optional
                             "session_number": "", # optional
                             "session_label": "", # optional
                             "task_label": "", # mandatory for functional data
                             "acquisition_number": "", # for Multiecho
                             "acquisition_label": "", # optional
                             "pe_direction_label": "", # optional
                             "run_index": ""} # optional

    def __init__(self, bids_config=default_configuration, format_precision=2):
        """

        :param bids_config: Dictionary with subject number, subject label, session number,
        session label, task label, acquisition label, pe_direction label and run index."
        :param format_precision: Zeropadding of subject and session numbers.
        :returns: None
        :rtype: None

        """
        self.config = dict()
        self.config["subject_number"] = bids_config.get("subject_number", 1)
        self.config["session_number"] = bids_config.get("session_number", "")
        self.config["subject_label"] = bids_config.get("subject_label", "")
        self.config["session_label"] = bids_config.get("session_label", "")
        self.config["task_label"] = bids_config.get("task_label", "")
        self.config["acquisition_label"] = bids_config.get("acquisition_label", "")
        self.config["acquisition_number"] = bids_config.get("acquisition_number", "")
        self.config["pe_direction_label"] = bids_config.get("pe_direction_label", "")
        self.config["run_index"] = bids_config.get("run_index", "")

        self.format_precision = format_precision

        # A formatter function to account for sub-N, sub-0N or sub-00N.
        self.formatter = formatter(self.format_precision)

        # Specify the order of the tags according to the BIDS specification.
        self.__tags = (self.subject_tag, self.session_tag,
                       self.task_tag, self.acquisition_tag, self.pe_direction_tag, self.run_tag)

        for label in self.config.values():
            if label != "":
                self.check_label(label)


    @staticmethod
    def check_label(label):
        """
        Check a label for BIDS consistency. Labels may not contain symbols.

        :param label: target label
        :returns: label consistency
        :rtype: bool

        """
        if str(label).isalnum():
            return True

        error_msg = "Following label contains illegal character: %s" % str(label)
        raise BidsMalformedLabelError(error_msg)

    @property
    def subject_tag(self):
        """
        Generate subject tag according to the BIDS specification.
        The subject tag is obligatory. It must contain a subject number.

        :returns: Subject tag
        :rtype: string

        """
        label = self.config["subject_label"]
        number = self.formatter(self.config["subject_number"])
        tag = "{0}-{1}{2}".format(self.bids_abbreviations["subject"],
                                  label,
                                  number)
        return tag

    @property
    def session_tag(self):
        """
        Generate session tag according to the BIDS specification.
        The session tag is optional. It may contain only numbers, only
        labels, or both.

        :returns: Session tag
        :rtype: string

        """
        if self.config["session_label"] == "" and self.config["session_number"] == "":
            return ""

        label = self.config["session_label"]
        if self.config["session_number"] is not "":
            number = self.formatter(self.config["session_number"])
        else:
            number = ""

        tag = "{0}-{1}{2}".format(self.bids_abbreviations["session"],
                                  label,
                                  number)
        return tag

    @property
    def task_tag(self):
        """
        Generate acquisition tag according to the BIDS specification.
        The acquisition tag is optional. It may be used to distinguish a specific
        type of acquisition, as in "singleband" for a singleband reference scan,
        for example.

        :returns: Acquisition tag
        :rtype: string
        """
        if self.config["task_label"] == "":
            return ""
        else:
            return "{0}-{1}".format(self.bids_abbreviations["task"],
                                    self.config["task_label"])


    @property
    def acquisition_tag(self):
        """
        Generate acquisition tag according to the BIDS specification.
        The acquisition tag is optional. It may be used to distinguish a specific
        type of acquisition, as in "singleband" for a singleband reference scan,
        for example.

        :returns: Acquisition tag
        :rtype: string
        """

        if self.config["acquisition_label"] == "" and self.config["acquisition_number"] == "":
            return ""

        label = self.config["acquisition_label"]
        if self.config["acquisition_number"] is not "":
            acq_formatter = formatter(precision=2)
            number = acq_formatter(self.config["acquisition_number"])
        else:
            number = ""

        tag = "{0}-{1}{2}".format(self.bids_abbreviations["acquisition"],
                                  label,
                                  number)
        return tag

    @property
    def pe_direction_tag(self):
        """
        Generate acquisition tag according to the BIDS specification.
        The acquisition tag is optional. It may be used to distinguish a specific
        type of acquisition, as in "singleband" for a singleband reference scan,
        for example.

        :returns: PE direction tag
        :rtype: string
        """
        if self.config["pe_direction_label"] == "":
            return ""
        else:
            return "{0}-{1}".format(self.bids_abbreviations["pe_direction"],
                                    self.config["pe_direction_label"])

    @property
    def run_tag(self):
        """
        Generate run tag according to the BIDS specification.
        The run index tag is optional. Use it to differentiate between runs of the
        same experiment.
        Run indices are formatted with 2 units of precision.

        :returns: Run tag
        :rtype: string
        """
        if self.config["run_index"] == "":
            return ""
        else:
            run_formatter = formatter(precision=2)
            return "{0}-{1}".format(self.bids_abbreviations["run"],
                                    run_formatter(self.config["run_index"]))

    @property
    def tag(self):
        """
        Generates the filename BIDS tag without yet specifying the scan type or file extension.

        :returns: Full tag (without scan type specifications.)
        :rtype: string

        """
        sep = self.bids_tag_separator
        return functools.reduce(
            lambda x, y: x + y,
            map(lambda x: x + sep if x is not "" else "", self.__tags))[:-1]


class AnatomicalBidifyer(Bidifyer):
    bids_canonical_directory = "anat"
    bids_canonical_endings = ("T1w", "T2w", "T1rho",
                              "T1map", "T2map",
                              "FLAIR", "FLASH",
                              "PD", "PDmap",
                              "PDT2", "inplaneT1", "inplaneT2",
                              "angio", "defacemask",
                              "SWImag", "SWIphase")

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class FunctionalBidifyer(Bidifyer):
    bids_canonical_directory = "func"
    bids_canonical_endings = ("bold", "sbref")

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        if self.config["task_label"] == "":
            error_msg = "Functional Data require a proper task label."
            raise BidsInconsistentNamingError(error_msg)


class PhysiologicalBidifyer(Bidifyer):
    # Physiological Data also goes to the functional directory.
    bids_canonical_directory = "func"
    bids_canonical_endings = ("physio")

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class DiffusionBidifyer(Bidifyer):
    bids_canonical_directory = "dwi"
    bids_canonical_endings = ("dwi")

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

class FieldMapBidifyer(Bidifyer):
    bids_canonical_directory = "fmap"
    bids_canonical_endings = ("phasediff", "magnitude1")

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
