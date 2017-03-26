# Time-stamp: <2017-03-26 18:37:29 danielpgomez>
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
import re
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

def formatter(precision=None):
    """
    Formatter returns a formatting function for a given precision.
    Ex. f =formatter(2) => f(3) = '03'
    Ex. f =formatter(5) => f(3) = '00003'

    :param precision: number of digits for formatter
    :returns: a lambda function that formats text.
    :rtype: function

    """
    precision = precision or 2
    form = "{" + ":0{}d".format(precision) + "}"
    return lambda x: form.format(int(x)) if x is not "" else ""

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
                 subject_index=None, session_index=None):
        """
        Parse configuration and verify inputs.

        :param input_dir: Toplevel directory to run Dac2Bids
        :param output_dir: Target output directory for BIDS NIfTIs.
        :param ignore_dirs: File or list of directories to ignore
        :param skip_incomplete: Skip series with incomplete volumes.
        :param subject_index: Subject index. If None, guess from input_dir.
        :param session_index: session index. If None, guess from output_dir.
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

        # FIXME Add automatic checks to read subject and session indexs
        # from the input directory, if subject and session indexs are None.
        self.subject_index = subject_index
        self.session_index = session_index

    def autocheck_subject(self):
        """
        Attempt to automatically detect subject index from DACs
        scheduler naming convention.
        """
        submatch = re.search('(?<=sub-x)\d+', self.input_dir)
        if submatch:
            return int(submatch.group(0))

    def autocheck_session(self):
        """
        Attempt to automatically detect subject index from DACs
        scheduler naming convention.
        """
        sesmatch = re.search('(?<=ses-mri-X)\d+', self.input_dir)
        if sesmatch:
            return int(sesmatch.group(0))


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

    # Bids naming conventions change every other week.
    bids_abbreviations = {"subject" :"sub",
                          "session" :"ses",
                          "task" :"task",
                          "acquisition" :"acq",
                          "pe_direction": "dir", # Phase encoding, for TOPUP.
                          "run" :"run"}

    bids_tag_separator = "_"

    default_configuration = {"subject_index": 1, # mandatory
                             "subject_label": "", # optional
                             "session_index": "", # optional
                             "session_label": "", # optional
                             "task_label": "", # mandatory for functional data
                             "acquisition_index": "", # for Multiecho
                             "acquisition_label": "", # optional
                             "pe_direction_label": "", # optional
                             "run_index": ""} # optional

    def __init__(self, bids_config=default_configuration, format_precision=2):
        """

        :param bids_config: Dictionary with subject index, subject label, session index,
        session label, task label, acquisition label, pe_direction label and run index."
        :param format_precision: Zeropadding of subject and session indexs.
        :returns: None
        :rtype: None

        """
        self.config = dict()
        self.config["subject_index"] = bids_config.get("subject_index", 1)
        self.config["session_index"] = bids_config.get("session_index", "")
        self.config["subject_label"] = bids_config.get("subject_label", "")
        self.config["session_label"] = bids_config.get("session_label", "")
        self.config["task_label"] = bids_config.get("task_label", "")
        self.config["acquisition_label"] = bids_config.get("acquisition_label", "")
        self.config["acquisition_index"] = bids_config.get("acquisition_index", "")
        self.config["pe_direction_label"] = bids_config.get("pe_direction_label", "")
        self.config["run_index"] = bids_config.get("run_index", "")

        self.format_precision = format_precision

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

    def __abstract_tag(self, target_tag, precision=None):
        """
        Generate any BIDS Tag.
        """
        tagname = self.bids_abbreviations.get(target_tag, "")
        label = self.config.get(target_tag + "_label", "")
        index = self.config.get(target_tag + "_index", "")

        if all(x == "" for x in (label, index)):
            return ""

        return "{0}-{1}{2}".format(tagname, label, formatter(precision)(index))


    @property
    def subject_tag(self):
        """
        Generate subject tag according to the BIDS specification.
        The subject tag is obligatory. It must contain a subject number.

        :returns: Subject tag
        :rtype: string

        """
        return self.__abstract_tag("subject", self.format_precision)

    @property
    def session_tag(self):
        """
        Generate session tag according to the BIDS specification.
        The session tag is optional. It may contain only numbers, only
        labels, or both.

        :returns: Session tag
        :rtype: string

        """
        return self.__abstract_tag("session", self.format_precision)

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
        return self.__abstract_tag("task")

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
        return self.__abstract_tag("acquisition")

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
        return self.__abstract_tag("pe_direction")

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
        return self.__abstract_tag("run")


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
