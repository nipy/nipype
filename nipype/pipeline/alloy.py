# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This is the alloy pipeline module, as adapted from the Alloy Matlab script.  The initial development of this relies on afni, suma and fsl command classes generated in nipypye/interfaces/, but should be expanded to include commands from spm and other programs as well.  Finally, there should be a GUI designed to maximize usability.
"""

import os

import nipype.interfaces.afni as afni

from nipype.interfaces.base import CommandLine

# XXX Hardcode these params for now.  Eventually we should get them
# from dicom headers (specifically for EPI dicom conversion).
num_slices = 24
num_images = 302
TR = 1370

# more variables currently hardcoded.  these should be determined
# by system, default variable file or user input
data_path = '/home/despo/dte/Alloy/Template'
num_cores = 4
nifti_folder = 'NIfTI'
behavior_folder = 'Behavior'
total_folder = 'Total'
extension = 'nii.gz'
data_extension = 'txt'
d_extension = 'txt'

anat_tag = 'T1'
func_tag = 'EPI'
data_tag = 'Data'
mean_tag = 'Mean'
mask_tag = 'Mask'
coreg_tag = 'Coreg'
md1d_tag = 'MD1D'
oned_tag = '1D'
smooth_tag = 'Smooth'
cut_tag = 'Cut'
brain_tag = 'Brain'

afni_to3d_datatype_anat = 'anat'
afni_to3d_datatype_func = 'epan'
afni_to3d_datum = 'float'
afni_3dresample_orient = 'RPI'

name_delimiter = '-'
ext_delimiter = '.'
irrelevant_prefix = '.'


class DataFile(object):
    """A DataFile object contains all the info to access data files

    Parameters
    ----------
    data_path : string
        root path to the data directory
    subject : string
        subject ID or ''
    session : {'2', 'T', None}
        session identifier character
    file_type : {'NIfTI', 'DICOM', 'Behavior'}
        data file type
    selectors : list of strings
        unique filetype identifying strings
    extension : list of strings
        file name extension strings

    """

    def __init__(self, data_path=None, subject=None,
                 session=None, file_type=None,
                 selectors=[], extension=[]):
        self.data_path = data_path
        self.subject = subject
        self.session = session
        self.file_type = file_type
        self.selectors = selectors
        self.extension = extension

    def __repr__(self):
        rep = 'DataFile: \n\t%s, \n\t%s, %s, %s, %s' % \
            (self.data_path, self.subject, self.session, 
             self.file_type, self.name())
        return rep

    def name(self):
        """Generate the file or folder name using selectors and extension.

        For a folder, no extensions should be present, so it will skip
        adding an extension.
        """
        name_main = name_delimiter.join(self.selectors)
        if self.extension:
            name_list = self.extension[:]
            name_list.insert(0,name_main)
            name_full = ext_delimiter.join(name_list)
        else:
            name_full = name_main

        return name_full

    def abspath(self):
        return os.path.join(self.data_path, self.subject, self.session,
                            self.file_type, self.name())

    def partpath(self, num_paths):
        if num_paths is 1:
            return self.data_path
        if num_paths is 2:
            return os.path.join(self.data_path, self.subject)
        if num_paths is 3:
            return os.path.join(self.data_path, self.subject, self.session)
        if num_paths is 4:
            return os.path.join(self.data_path, self.subject, self.session,
                                self.file_type)

    def copy(self):
        new = DataFile()
        new.data_path = self.data_path
        new.subject = self.subject
        new.session = self.session
        new.file_type = self.file_type
        new.selectors = self.selectors[:]
        new.extension = self.extension[:]
        return new


def afni_dicom_convert(in_file_info):
    """Convert a set of dicom files into nifti files.

    Parameters
    ----------
    in_file_info : DataFile class

    """

    # Get list of dicom files
    dicom_list = get_data_selection(in_file_info)

    for dicom in dicom_list:

        nifti_file = dicom.copy()
        nifti_file.file_type = nifti_folder
        nifti_file.extension = extension.split(ext_delimiter)

        if dicom.selectors.__contains__(anat_tag):

            cmd1 = afni.To3d(
                datatype=afni_to3d_datatype_anat,
                datum=afni_to3d_datum,
                session=nifti_file.partpath(4),
                prefix=nifti_file.name(),
                infiles=dicom.abspath() + '/*.dcm')

        if dicom.selectors.__contains__(func_tag):

            td = {
                'slice_order':'zt',
                'nz':num_slices,
                'nt':num_images,
                'TR':TR,
                'tpattern':'alt+z2'}

            cmd1 = afni.To3d(
                datatype=afni_to3d_datatype_func,
                skip_outliers=True,
                assume_dicom_mosaic=True,
                datum=afni_to3d_datum,
                time_dependencies=td,
                session=nifti_file.partpath(4),
                prefix=nifti_file.name(),
                infiles=dicom.abspath() + '/*.dcm')

        # command to deoblique and center volume
        cmd2 = afni.Threedrefit(
            deoblique=True,
            xorigin='cen',
            yorigin='cen',
            zorigin='cen',
            infile=nifti_file.abspath())

        # 3drefit only writes its output to the directory it was run in.
        # move the new file back to the appropriate directory
        cmd3 = CommandLine('mv', '-f',
            nifti_file.name(),
            nifti_file.abspath())

        # command to change volume orientation from LPI to RPI
        nifti_file_rpi = nifti_file.copy()
        nifti_file_rpi.selectors.append('RPI')

        cmd4 = afni.Threedresample(
            orient=afni_3dresample_orient,
            outfile=nifti_file_rpi.abspath(),
            infile=nifti_file.abspath())

        cmd5 = CommandLine('mv', '-f',
            nifti_file_rpi.abspath(),
            nifti_file.abspath())

        cmds = [cmd1, cmd2, cmd3, cmd4, cmd5]

        run_commands(cmds,nifti_file)

    out_file_info = in_file_info.copy()
    out_file_info.file_type = nifti_folder
    out_file_info.extension = extension.split(ext_delimiter)

    return out_file_info


def file_organize(in_file_info):

    in_file_info.session = '2'
    in_file_info.extension = ['']

    in_file_info.file_type = nifti_folder
    in_file_info.selectors = [anat_tag]

    # collect all the anatomical file names
    t1_list = get_data_selection(in_file_info)

    in_file_info.file_type = nifti_folder
    in_file_info.selectors = [func_tag]

    # collect all the functional file names
    epi_list = get_data_selection(in_file_info)

    in_file_info.file_type = behavior_folder
    in_file_info.selectors = [data_tag]

    # collect all the behavioral file names
    data_list = get_data_selection(in_file_info)

    for t1_file in t1_list:

        out_file = t1_file.copy()
        out_file.session = total_folder
        out_file.selectors = [t1_file.subject, anat_tag]

        try:
            os.mkdir(out_file.partpath(3))
        except OSError:
            pass

        cmd1 = [CommandLine('cp',
            t1_file.abspath(),
            out_file.abspath())]

        run_commands(cmd1,out_file)

    lastsubj = epi_list[0].subject
    counter = 0

    for epi_file in epi_list:

        if epi_file.subject == lastsubj:
            counter = counter + 1
        else:
            lastsubj = epi_file.subject
            counter = 1

        counter_string = counter.__str__()
        if counter_string.__len__() is 1:
            counter_string = ('00' + counter_string)
        if counter_string.__len__() is 2:
            counter_string = ('0' + counter_string)

        out_file = epi_file.copy()
        out_file.session = total_folder
        out_file.selectors = [epi_file.subject, func_tag, counter_string]

        try:
            os.mkdir(out_file.partpath(3))
        except OSError:
            pass

        cmd2 = [CommandLine('cp',
            epi_file.abspath(),
            out_file.abspath())]

        run_commands(cmd2,out_file)

    lastsubj = data_list[0].subject
    counter = 0

    for data_file in data_list:

        if data_file.subject == lastsubj:
            counter = counter + 1
        else:
            lastsubj = data_file.subject
            counter = 1

        counter_string = counter.__str__()
        if counter_string.__len__() is 1:
            counter_string = ('00' + counter_string)
        if counter_string.__len__() is 2:
            counter_string = ('0' + counter_string)

        out_file = data_file.copy()
        out_file.session = total_folder
        out_file.selectors = [data_file.subject, data_tag, counter_string]

        try:
            os.mkdir(out_file.partpath(3))
        except OSError:
            pass

        cmd3 = [CommandLine('cp',
            data_file.abspath(),
            out_file.abspath())]

        run_commands(cmd3,out_file)


def afni_mean(in_file_info):
    """Generate a mean image for a set of functional images.

    If this module is run, it should be immediately after the initial
    conversion and before the rest of the preprocessing pipeline.
    """

    # collect all the input file names
    in_list = get_data_selection(in_file_info)

    for in_file in in_list:

        out_file = in_file.copy()
        out_file.selectors = [in_file.subject, mean_tag]

        cmd1 = [afni.ThreedTstat(
            outfile=out_file.abspath(),
            infile=in_file.abspath())]

        run_commands(cmd1,out_file)

    out_file_info = in_file_info.copy()
    out_file_info.selectors = [mean_tag]

    return out_file_info


def afni_mask(in_file_info):
    """Generate a mask image for a set of functional images.

    This module should be run on a mean image for the corresponding
    functional image group.
    """

    # collect all the first EPI file names
    in_list = get_data_selection(in_file_info)

    for in_file in in_list:

        out_file = in_file.copy()
        out_file.selectors = [in_file.subject, mask_tag]

        cmd1 = [afni.ThreedAutomask(
            outfile=out_file.abspath(),
            infile=in_file.abspath())]

        run_commands(cmd1,out_file)

    out_file_info = in_file_info.copy()
    out_file_info.selectors = [mask_tag]

    return out_file_info


def afni_coreg(in_file_info):
    """Coregister functional images with a corresponding mean image.

    This module will run a functional image set with a mean image
    corresponding to the subject number.
    """

    # collect all the input file names
    in_list = get_data_selection(in_file_info)

    for in_file in in_list:
        if not in_file.selectors.__contains__(coreg_tag):

            base_file = in_file.copy()
            base_file.selectors = [in_file.subject, mean_tag]

            out_file = in_file.copy()
            out_file.selectors.append(coreg_tag)

            md1d_file = out_file.copy()
            md1d_file.selectors.append(md1d_tag)
            md1d_file.extension = [d_extension]

            oned_file = out_file.copy()
            oned_file.selectors.append(oned_tag)
            oned_file.extension = [d_extension]

            cmd1 = [afni.Threedvolreg(
                verbose = True,
                copy_origin = True,
                time_shift = True,
                basefile = base_file.abspath(),
                md1dfile = md1d_file.abspath(),
                onedfile = oned_file.abspath(),
                outfile = out_file.abspath(),
                infile = in_file.abspath())]

            run_commands(cmd1,out_file)

    out_file_info = in_file_info.copy()
    out_file_info.selectors = [coreg_tag]

    return out_file_info


def afni_smooth(in_file_info):
    """Smooth functional images.

    """

    # collect all the input file names
    in_list = get_data_selection(in_file_info)

    for in_file in in_list:
        if not in_file.selectors.__contains__(smooth_tag):

            out_file = in_file.copy()
            out_file.selectors.append(smooth_tag)

            cmd1 = [afni.Threedmerge(
                doall = True,
                gblur_fwhm = 5,
                outfile = out_file.abspath(),
                infile = in_file.abspath())]

            run_commands(cmd1,out_file)

    out_file_info = in_file_info.copy()
    out_file_info.selectors = [smooth_tag]

    return out_file_info


def afni_t1_align(in_file_info):
    """align anatomical to functional mean image.

    """

    # collect all the input file names
    anat_list = get_data_selection(in_file_info)

    for anat_file in anat_list:

        cut_file = anat_file.copy()
        cut_file.selectors.append(cut_tag)

        cmd1 = afni.ThreedZcutup(
               keep = {'from':80,'to':240},
               outfile = cut_file.abspath(),
               infile = anat_file.abspath())

        brain_file = anat_file.copy()
        brain_file.selectors.append(brain_tag)

        cmd2 = afni.ThreedSkullStrip(
               outfile = brain_file.abspath(),
               infile = cut_file.abspath())

        mean_file = anat_file.copy()
        mean_file.selectors = [anat_file.subject, mean_tag]

        meanrs_file = mean_file.copy()
        meanrs_file.selectors.append('RS')

        cmd3 = afni.Threedresample(
               rsmode = 'Cu',
               gridfile = brain_file.abspath(),
               outfile = meanrs_file.abspath(),
               infile = mean_file.abspath())

        meanbrain_file = meanrs_file.copy()
        meanbrain_file.selectors.append('Br')

        cmd4 = afni.ThreedSkullStrip(
               outfile = meanbrain_file.abspath(),
               infile = meanrs_file.abspath())

        cmd5 = afni.ThreedBrickStat(
               automask = True,
               percentile = {'p0':90.0,'pstep':1,'p1':90.0},
               infile = meanbrain_file.abspath())

        meanthresh_file = meanbrain_file.copy()
        meanthresh_file.selectors.append('Thr')

        cmd6 = afni.Threedcalc(
               infile_a = meanbrain_file.abspath(),
               expr = '\'min(1,(a/-999.0))\'',
               session = meanthresh_file.partpath(4),
               datum = 'float',
               outfile = meanthresh_file.name())

        t1align_file = brain_file.copy()
        t1align_file.selectors.append('Align')

        trans_matrix_file = anat_file.copy()
        trans_matrix_file.selectors = [anat_file.subject, oned_tag]
        trans_matrix_file.extension = d_extension.split(ext_delimiter)

        cmd7 = afni.ThreedAllineate(
               lpc = True,
               weight_frac = 1.0,
               verbose = True,
               warp = 'aff',
               maxrot = 6,
               maxshf = 10,
               source_automask = 4,
               transform_matrix = trans_matrix_file.abspath(),
               base = meanthresh_file.abspath(),
               outfile = t1align_file.abspath(),
               infile = brain_file.abspath(),
               weight = meanthresh_file.abspath())

        cmds = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7]

        out_file = anat_file.copy()
        out_file.selectors = [brain_tag]

        run_commands(cmds,out_file)

    out_file_info = in_file_info.copy()
    out_file_info.selectors = [brain_tag]

    return out_file_info


# XXXXX UPGRADES NEEDED ELSEWHERE
    # running the commands needs to be structured in such a way that
    # the output of each command can be accessed independently of
    # this script.  this could be achieved by .run saving a set of
    # variables, including cmdline, stderr, stdout and maybe others.


def run_commands(cmd_list, out):

    # continue if the output file does not exist
    if not os.path.exists(out.abspath()):

        # make the directory that will contain the output file, ignore errors
        try:
            os.mkdir(out.partpath(4))
        except OSError:
            pass

        for cmd in cmd_list:
            # execute the given command and print results to screen
            # XXXXX UPGRADES NEEDED ELSEWHERE
                # There should be a way to compile the command
                # before it is run.
            print 'Executing command:', cmd.cmdline
            results = cmd.run()
            print results.runtime.stderr + results.runtime.stdout


def get_data_selection(in_file_info):
    """Build a list of specific data files using the selection criteria.

    Before using this function, the data should have already been
    sorted and renamed according to the established naming convention:

        data_path/subject/session/file_type/selectors

    For example:

        /home/despo/dte/Alloy/Template/101/20080813/DICOM/008-EPI-96-13TR-2

    Where:
        data_path = /home/despo/dte/Alloy/Template
        subject = 101
        session = 20080813
        file_type = DICOM
        data_selection = [008, EPI, 96, 13TR, 2]

    Parameters
    ----------

    in_selection : DataFile class
    """

    # XXX NB: Reevaluate folder naming convention and selection

    # TO DO:
    # - altering selection
    #   - selection should be modified such that if the next value to check
    #     contains a valid selection criteria, that should be applied to the
    #     entries.  That is, if the value is '2', and there are entries that
    #     begin with '2', those entries should be selected.  If the value is
    #     empty, all values in that category should be added to the list. 

    file_list = []
    filters = ''

    for (path,dirs,files) in os.walk(in_file_info.data_path):
        path = path.lstrip(in_file_info.data_path)
        path = path.split(os.path.sep)
        dirs.sort()
        files.sort()

        if path == ['']:
            filters = in_file_info.subject
        elif len(path) is 1:
            filters = in_file_info.session
        elif len(path) is 2:
            filters = in_file_info.file_type
        elif len(path) is 3:
            filters = ''
            if not in_file_info.extension:
                files = dirs[:]

            for file_name in files:

                file_name_parts = file_name.split(name_delimiter)

                last_entry = file_name_parts.pop(-1)
                last_entry = last_entry.split(ext_delimiter)
                file_name_parts.append(last_entry.pop(0))
                criteria = 0

                for entry in file_name_parts:

                    if entry in in_file_info.selectors or in_file_info.selectors == ['']:
                        if last_entry == in_file_info.extension or in_file_info.extension == ['']:
                            criteria = 1

                # select data files that match the selection criteria
                if file_name_parts[0] != irrelevant_prefix and criteria is 1:

                    datafile = DataFile()
                    datafile.data_path = in_file_info.data_path
                    datafile.subject = path[0]
                    datafile.session = path[1]
                    datafile.file_type = path[2]
                    datafile.selectors = file_name_parts[:]
                    datafile.extension = last_entry[:]
                    file_list.append(datafile)

            dir_remove = dirs[:]

            for dir_name in dir_remove:
                dirs.remove(dir_name)

        dir_remove = []

        for dir_name in dirs:
            if not dir_name.startswith(filters):
                dir_remove.append(dir_name)

        for dir_name in dir_remove:
            dirs.remove(dir_name)

    return file_list


if __name__ == '__main__':
     dicom_file_info = DataFile(data_path,'','2','DICOM',['T1', 'EPI'],[])

     out_file_info = afni_dicom_convert(dicom_file_info)

     file_organize(out_file_info)

     start_file_info = DataFile(data_path,'','T','NIfTI',['001'],extension.split(ext_delimiter))
     mean_file_info = afni_mean(start_file_info)
     mask_file_info = afni_mask(mean_file_info)

     start_file_info.selectors = ['EPI']

     coreg_file_info = afni_coreg(start_file_info)
     smooth_file_info = afni_smooth(coreg_file_info)

     t1_file_info = DataFile(data_path,'101','T','NIfTI',['T1'],extension.split(ext_delimiter))

     brain_file_info = afni_t1_align(t1_file_info)

