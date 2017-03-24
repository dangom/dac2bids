# Time-stamp: <2017-03-24 01:57:05 danielpgomez>
"""
Dac2Bids generates a YAML configuration file for dcm2niibatch
from a root folder with subfolders of DICOM files.
"""
class UnproperDicomSortingError(Exception):
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




class DicomDispatcher:
    """
    Contains all logic and heuristics to decide whether a folder contains
    anatomical, diffusion, functional or physiological data (or field maps).
    """

class DicomParser:
    """
    Provide functionality to extract *relevant* Dicom information.
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


class AnatomicalParser(DicomParser):
    def __init__(self):
        pass

class FunctionalParser(DicomParser):
    def __init__(self):
        pass

class PhysiologicalParser(DicomParser):
    def __init__(self):
        pass


class DiffusionParser(DicomParser):
    def __init__(self):
        pass


def lsdirs(currfolder):
    """
    List all directories in a folder.
    Ignore files.
    """
    return filter(lambda x:
                  os.path.isdir(os.path.join(currfolder, x)),
                  os.listdir(currfolder))

def has_subdirectory(folder):
    """
    Return true if a folder has a subdirectory.
    Ignore hidden directories (such as .git, for example)
    """
    for input, dirs, files in os.walk(folder):
        if dirs and not all(d[0]=='.' for d in dirs):
            return True
        else:
            return False
