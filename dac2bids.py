#!/usr/bin/env python

# Daniel Gomez 29.08.2016
# generates configuration for dcm2niibatch
# from a nested folder with dicom files.

import random
import re
import os.path
import optparse
import yaml
import dicom


# will need to create a nifti file for each directory in folder.
# note the implicit assumption that all folders contain only one series,
# echo or whatever.
# to do that, check some information from the dicom.

# to build a BIDS file, we need the following info:
# 1. is the nifti going to anat, func or fmap?
# 2. does it belong to MB acquisition or to the mbme?
# 3. what echo is it?
# 4. is it a magnitude or phase image?!
# 5. if func, is it resting-state or task? For that we'll have to
# look at the protocol name. Isn't it a terrible design error that
# we cannot know what the data was used for from the DICOMs?


# get all directories in a given folder
def lsdirs(currfolder):
    """
    List all directories in a folder.
    Ignore files.
    """
    return filter(lambda x:
                  os.path.isdir(os.path.join(currfolder, x)),
                  os.listdir(currfolder))


def mag_or_phase(dicomImgTypeTag):
    """
    Tests if a DICOM image is magnitude or phase.
    dicomImgTypeTag is the string from the DICOM ImgTypeTag.
    """
    # Magnitude or phase?
    if 'M' in dicomImgTypeTag:
        return 'magnitude'
    elif 'P' in dicomImgTypeTag:
        return 'phase'
    else:
        return 'unknown'

RANDOM_FILE_MEMO = {}
def get_random_file(folder):
    """
    Returns a random file from a folder.
    It memorizes the file so that multiple calls to the function always return the same file.
    (For Python 3 we could have used @functools.lru_cache(maxsize=None) as a decorator and avoid
    having memo code in the implementation)
    """
    if folder not in RANDOM_FILE_MEMO:
        RANDOM_FILE_MEMO[folder] = random.choice(os.listdir(folder))
    return os.path.join(folder, RANDOM_FILE_MEMO[folder])


def parse_from_x_protocol(pattern, dicomfile):
    """
    Siemens writes a protocol structure as text into each DICOM file.
    This structure is necessary to recreate a scanning protocol from a DICOM, since the
    DICOM information alone wouldn't be sufficient.
    This function extracts values from the dicomfile according to a given pattern.
    """
    with open(dicomfile, 'rb') as openfile:
        regex = '^' + pattern + '\t = \t(.*)\n'
        rx = re.compile(regex.encode('utf-8'))
        for line in openfile:
            match = rx.match(line)
            if match:
                return int(match.group(1).decode('utf-8'))


def get_number_of_repetitions_from_x_protocol(dicomfile):
    return parse_from_x_protocol('lRepetitions', dicomfile)


def get_number_of_echoes_from_x_protocol(dicomfile):
    return parse_from_x_protocol('lContrasts', dicomfile)


def is_incomplete_acquisition(folder):
    """
    If a scan was aborted in the middle of the experiment, it is likely that DICOMs will
    land in the PACS anyway. We want to avoid converting these incomplete directories.
    This function checks the number of measurements specified in the protocol against the
    number of DICOMs.
    """
    randfile = get_random_file(folder)
    nrep = get_number_of_repetitions_from_x_protocol(randfile)
    return nrep > len(os.listdir(folder)) - 1


def is_multiecho(folder):
    randfile = get_random_file(folder)
    return get_number_of_echoes_from_x_protocol(randfile) > 1


# NEEDS refactoring. 
def parse_protocols(currfolder):
    """
    Takes a random DICOM image from currfolder and extracts
    relevant information for dcm2niix conversion (and for the BIDS format.)
    """

    # Initialize empty currfolder.
    dirs = dict.fromkeys(lsdirs(currfolder))
    dirs = {k:v for k,v in dirs.items() if 'localizer' not in k}

    for protocol in dirs.keys():
        # Get a random dicom from the folder.
        filepath = os.path.join(currfolder,
                                protocol,
                                random.choice(os.listdir(
                                    os.path.join(currfolder, protocol))))
        try:
            dicomfile = dicom.read_file(filepath)
        except IOError:
            print('File in folder ' + protocol + ' is not a dicom.')
            continue

        # Attempt to grab enough information from dicoms.
        try:
            seq = dicomfile.ScanningSequence
            echo = dicomfile.EchoNumbers
            desc = dicomfile.SeriesDescription
            imgtype = dicomfile.ImageType
            seqname = dicomfile.SequenceName
            # prot = dicomfile.ProtocolName
        except AttributeError:
            print('Found weird dicom in folder ' + protocol)
            # Check for special physiological dicoms.
            try:
                # imgcomment = dicomfile.ImageComments
                imgtype = dicomfile.ImageType
                outfolder = 'physio'
                seq = 'physio'
                echo = 0
                experiment = 'physio'
                # If it is weird and isn't Physio, skip folder.
            except AttributeError:
                print('Found a really weird dicom... Check manually.')
                # Skip folder.
                continue

        # Simple logic for the information to create output filename.
        acq = ''
        # Functional images
        if seq == 'EP':
            outfolder = 'func'
            if 'Resting' in desc:
                experiment = 'task-rest'
            elif 'Task' in desc:
                experiment = 'task-stroop'
            else:
                experiment = 'unknown'
            if get_number_of_echoes_from_x_protocol(filepath) > 1:
                acq = 'acq-mbme'
            else:
                acq = 'acq-mb'
        elif 'GR' in seq and 'IR' not in seq:
            # Field map
            if seqname == '*fm2d2r':
                outfolder = 'fmap'
                experiment = ''
                # T2 star mapping
            elif seqname == '*fl3d11r':
                outfolder = 'anat'
                experiment = 'T2starw'
        elif 'IR' in seq:
            outfolder = 'anat'
            experiment = 'T1w'
        elif outfolder not in {'anat', 'func', 'fmap'}:
            outfolder = 'unknown'
            experiment = 'unknown'

        imgtype = mag_or_phase(imgtype)

        # add to dict
        dirs[protocol] = {'imgtype': imgtype,
                          'outfolder': outfolder,
                          'experiment': experiment,
                          'echo': echo,
                          'acq': acq}
    return dirs


def bids_opts():
    """
    OPTS is a structure accepted by dcm2niibatch converter.
    This function returns a reasonable configuration for BIDS.
    """
    opts = {'isGz': True,
            'isFlipY': False,
            'isVerbose': False,
            'isCreateBIDS': True,
            'isOnlySingleFile': False}
    return opts


def create_yaml(inputfolder, outputfolder, subnum=0, sesnum=0, skipfmap=False):
    """
    Generate a yaml file compatible with dcm2niibatch and the BIDS format.
    Takes an inputfolder tree containing folders with dicom files.
    Folders in inputfolder are assumed to contain a single dataset.
    """
    inputdict = parse_protocols(inputfolder)

    # formatted subject number and session number
    sub = 'sub-' + '%02d' % (subnum,)
    ses = 'ses-' + '%02d' % (sesnum,)

    # The pydict will be converted to a yaml file.
    pydict = {'Options': bids_opts(), 'Files': []}

    for protocol, config in inputdict.items():

        # if config['imgtype'] == 'phase':
        #     continue

        echonum = '%02d' % (config['echo'],)

        inputdirectory = os.path.join(inputfolder, protocol)

        if is_incomplete_acquisition(inputdirectory):
            continue

        outputdirectory = os.path.join(outputfolder, sub, ses, config['outfolder'])

        filename = sub + '_' + ses

        if config['outfolder'] == 'func':
            #continue # remove this
            filename += '_' + config['experiment'] + '_' + config['acq'] + echonum
            filename += '_bold'
            filename += '_' + config['imgtype'] + echonum

        if config['outfolder'] == 'anat':
            #continue #remove this
            filename += '_' + config['experiment']
            if config['experiment'] == 'T2starw':
                filename += '_' + config['imgtype'] + echonum

        if config['outfolder'] == 'fmap':
            if skipfmap:
                dummy = 0 #continue
            else:
                filename += '_' + config['imgtype'] + echonum

        if config['outfolder'] is not 'unknown':
            filedict = {'in_dir': os.path.abspath(inputdirectory),
                        'out_dir': os.path.abspath(outputdirectory),
                        'filename': filename}
            pydict['Files'].append(filedict)

    return yaml.safe_dump(pydict, default_flow_style=False)


# # define custom tag handler
# def join(loader, node):
#     seq = loader.construct_sequence(node)
#     return ''.join([str(i) for i in seq])

# # register the tag handler
# yaml.add_constructor('!join', join)
# # using your sample data
# test = yaml.load("""
# paths:
#     root: &BASE /path/to/root/
#     patha: !join [*BASE, a]
#     pathb: !join [*BASE, b]
#     pathc: !join [*BASE, c]
# """)

# NEEDS refactoring. Change deprecated OptionParser to ArgParser.
def main():
    p = optparse.OptionParser()
    p.add_option('--inputfolder', '-i', default='.', help="Input folder of dicoms")
    p.add_option('--outputfolder', '-o', default='./out/', help="Output folder for niftis")
    #p.add_option('--yaml', '-y', default='./batch.yaml', help="Name of generated config file.")
    p.add_option('--sub', '-s', default=1, type="int", help="The subject number")
    p.add_option('--ses', '-e', default=1, type="int", help="The session number")
    p.add_option('--skipfmap', '-f', action="store_true", help="Skips fieldmaps.")

    options, arguments = p.parse_args()

    yamlcontent = create_yaml(options.inputfolder,
                              options.outputfolder,
                              subnum=options.sub,
                              sesnum=options.ses,
                              skipfmap=options.skipfmap)

    yamlname = './sub-' + str(options.sub) + '_ses-' + str(options.ses) + '.yaml'
    with open(yamlname, 'w') as yamlfile:
        yamlfile.write(yamlcontent)


if __name__ == '__main__':
    main()
