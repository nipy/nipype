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
# by system or user input
data_path = '/home/despo/dte/Alloy/Template'
num_cores = 4
extension = '.nii.gz'


class DataFile(object):
    """A DataFile object contains all the path information to access a data file

    Parameters
    ----------
    data_path : string
        root path to the data directory
    subject : string
        subject ID or ''
    session : {'2', 'T', None}
        session identifier character
    name : XXX
        XXX
    file_type : {'NIfTI', 'DICOM', 'Behavior'}
        data file type

    """

    def __init__(self, data_path=None, subject=None, session=None, name=None, 
                 file_type=None):
        self.data_path = data_path
        self.subject = subject
        self.session = session
        self.file_type = file_type
        self.name = name # filename for nifti, directory for dicom

    def __repr__(self):
        rep = 'DataFile: \n\t%s, \n\t%s, %s, %s, %s' % \
            (self.data_path, self.subject, self.session, 
             self.file_type, self.name)
        return rep
    
    def abspath(self):
        return os.path.join(self.data_path, self.subject, self.session,
                            self.file_type, self.name)

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


def afni_dicom_convert(data_path, subject, session, file_type, data_selection):
    """Convert a set of dicom files into nifti files.

    Parameters
    ----------
    data_path : string
        path to the data directory
    subject : string
        subject ID. or ''
    session : {'2', 'T', None}
        session identifier character
    file_type : {'NIfTI', 'DICOM', 'Behavior'}
        data file type
    data_selection : string
        data identifier string

    """

    # Get list of dicom files
    dicom_list = get_data_selection(data_path, subject, session, file_type,
                                    data_selection)

    for dicom in dicom_list:
        filename = (dicom.subject + '-' + dicom.session + '-' + dicom.name
                    + extension)
        nifti_file = DataFile()
        nifti_file.data_path = dicom.data_path
        nifti_file.subject = dicom.subject
        nifti_file.session = dicom.session
        nifti_file.file_type = 'NIfTI'
        nifti_file.name = filename

        if data_selection == 'T1':

            cmd1 = afni.To3d(
                datatype='anat',
                datum='float',
                session=nifti_file.partpath(4),
                prefix=nifti_file.name,
                infiles=dicom.abspath() + '/*.dcm')

        if data_selection == 'EPI':

            td = {
                'slice_order':'zt',
                'nz':num_slices,
                'nt':num_images,
                'TR':TR,
                'tpattern':'alt+z2'}

            cmd1 = afni.To3d(
                datatype='epan',
                skip_outliers=True,
                assume_dicom_mosaic=True,
                datum='float',
                time_dependencies=td,
                session=nifti_file.partpath(4),
                prefix=nifti_file.name,
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
            nifti_file.name,
            nifti_file.abspath())

        # command to change volume orientation from LPI to RPI
        nifti_file_rpi = (nifti_file.partpath(4) + '/' +
                          nifti_file.name[0:-len(extension)] +
                          '-RPI' + extension)

        cmd4 = afni.Threedresample(
            orient='RPI',
            outfile=nifti_file_rpi,
            infile=nifti_file.abspath())

        cmd5 = CommandLine('mv', '-f',
            nifti_file_rpi,
            nifti_file.abspath())


        cmds = [cmd1, cmd2, cmd3, cmd4, cmd5]

        run_commands(cmds,nifti_file)


def file_organize(data_path):

    out_file = DataFile()

    # collect all the anatomical file names
    t1_list = get_data_selection(data_path,'','2','NIfTI','T1')

    # collect all the functional file names
    epi_list = get_data_selection(data_path,'','2','NIfTI','EPI')

    # collect all the behavioral file names
    data_list = get_data_selection(data_path,'','2','Behavior','Data')

    for t1_file in t1_list:

        out_file.data_path = t1_file.data_path
        out_file.subject = t1_file.subject
        out_file.session = 'Total'
        out_file.file_type = t1_file.file_type
        out_file.name = (t1_file.subject + '-T1' + extension)

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

        out_file.data_path = epi_file.data_path
        out_file.subject = epi_file.subject
        out_file.session = 'Total'
        out_file.file_type = epi_file.file_type
        out_file.name = (epi_file.subject + '-EPI-' + 
                         counter_string + extension)

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

        out_file.data_path = data_file.data_path
        out_file.subject = data_file.subject
        out_file.session = 'Total'
        out_file.file_type = data_file.file_type
        out_file.name = (data_file.subject + '-Data-' +
                         counter_string + '.txt')

        try:
            os.mkdir(out_file.partpath(3))
        except OSError:
            pass

        cmd3 = [CommandLine('cp',
            data_file.abspath(),
            out_file.abspath())]

        run_commands(cmd3,out_file)


def afni_mean(data_path):
    """Generate a mean image for a set of functional images.

    If this module is run, it should be immediately after the initial
    conversion and before the rest of the preprocessing pipeline.
    """

    # collect all the first EPI file names
    data_selection = ('001' + extension)
    epi_list = get_data_selection(data_path,'','T','NIfTI',data_selection)

    for epi_file in epi_list:

        out_file = DataFile()
        out_file.data_path = epi_file.data_path
        out_file.subject = epi_file.subject
        out_file.session = epi_file.session
        out_file.file_type = epi_file.file_type
        out_file.name = (epi_file.subject + '-Mean' + extension)

        cmd1 = [afni.ThreedTstat(
            outfile=out_file.abspath(),
            infile=epi_file.abspath())]

        run_commands(cmd1,out_file)

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
            results = cmd.run()
            print 'Executing command:', cmd.cmdline
            print results.runtime.errmessages + results.runtime.messages


def get_data_selection(data_path, subject, session, file_type, data_selection):
    """Build a list of specific data files from the data_dir directory.

    Before using this function, the data should have already been
    sorted and renamed according to the established naming convention:

        data_path/subject/session/file_type/data_selection

    For example:

        /home/despo/dte/Alloy/Template/101/20080813/DICOM/008-EPI-96-13TR-2

    Where:
        data_path = /home/despo/dte/Alloy/Template
        subject = 101
        session = 20080813
        file_type = DICOM
        data_selection = 008-EPI-96-13TR-2

    Parameters
    ----------
    data_path : string
        path to the data directory
    subject : string
        subject ID. or ''
    session : {'2', 'T', None}
        session identifier character
    file_type : {'NIfTI', 'DICOM', 'Behavior'}
        data file type
    data_selection : string
        data identifier string

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

    list_one = os.listdir(data_path)
    list_one.sort()

    for entry_one in list_one:
	entry_path_one = os.path.join(data_path, entry_one)

	# select directories whose names are 3 characters long
        if os.path.isdir(entry_path_one) and len(entry_one) is 3:

	    list_two = os.listdir(entry_path_one)
	    list_two.sort()

	    for entry_two in list_two:
                entry_path_two = os.path.join(entry_path_one, entry_two)

                # select directories that start with the session char
                # (unless no session char was entered)
		if os.path.isdir(entry_path_two) and \
                    (entry_two[0] is session or session is None):

		    # add file type folder to directory path
		    entry_path_three = os.path.join(entry_path_two, file_type)

                    try:
                        list_four = os.listdir(entry_path_three)
		        list_four.sort()

		        for entry_four in list_four:

			    entry_four_parts = entry_four.split('-')

			    criteria = 0;

			    for entry in entry_four_parts:
			        if entry == data_selection:
			            criteria = 1;

			    # select data files that match the selection criteria
		            if entry_four[0] is not '.' and criteria is 1:

			    # Split the path into it's directory components and
                            # get the last two directories which will be the
                            # subject_id and the session_id
                                elements = entry_path_three.split(os.path.sep)
                                datafile = DataFile()
                                datafile.data_path = data_path
                                datafile.name = entry_four
                                datafile.subject = elements[-3]
                                datafile.session = elements[-2]
                                datafile.file_type = elements[-1]
                                file_list.append(datafile)

		    except OSError:
                        pass

    return file_list


if __name__ == '__main__':
     #afni_dicom_convert(data_path, '', '2', 'DICOM', 'T1')
     #afni_dicom_convert(data_path, '', '2', 'DICOM', 'EPI')
     #file_organize(data_path)
     afni_mean(data_path)
