# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os, sys
import commands, tempfile


class XnatInterface:
    def __init__(self, server, user, password):
        self.__rest_account = "java -jar %s -host %s -u %s -p %s -m "%(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xnat_tools/lib/xdat-restClient-1.jar'), server, user, password)
        self.__server = server
        self.__user = user
        self.verbosity = 0

    def execute_get(self, uri):
        if self.verbosity > 0:    print self.__rest_account+'GET -remote '+uri
        return commands.getoutput(self.__rest_account+'GET -remote '+uri)

    def execute_get_csv(self, uri, column=0):
        if self.verbosity > 0:    print self.__rest_account+'GET -remote '+uri
        output = commands.getoutput(self.__rest_account+'GET -remote '+uri)
        if self.verbosity >= 1:    print output
        return [row.split(',')[column].replace('"', '') for row in output.split('\n')[1:]]

    def execute_put(self, uri):
        if self.verbosity > 0:    print self.__rest_account+'PUT -remote '+uri
        output = commands.getoutput(self.__rest_account+'PUT -remote '+uri)
        if self.verbosity >= 1:    print output

    def execute_delete(self, uri):
        if self.verbosity > 0:    print self.__rest_account+'DELETE -remote '+uri
        output = commands.getoutput(self.__rest_account+'DELETE -remote '+uri)
        if self.verbosity >= 1:    print output

    def projects(self):
        return [XnatProject(project_ID, self) for project_ID in self.execute_get_csv("'/REST/projects?format=csv'")]

    def project(self, project_ID):
        return XnatProject(project_ID, self)

    def __repr__(self):
        return '<Interface %s@%s>'%(self.__user, self.__server)

class XnatProject:
    def __init__(self, project_ID, interface):
        self.ID = project_ID
        self.interface = interface

    def subjects(self):
        return [XnatSubject(self.ID, subject_ID, self.interface) for subject_ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects?format=csv'"%self.ID)]

    def subject(self, subject_ID):
        return XnatSubject(self.ID, subject_ID, self.interface)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects?format=csv'")

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/files/%s"%(self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/files/%s"%(self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/files?format=csv'"%(self.ID))]

    def __repr__(self):
        return '<Project "%s">'%(self.ID)

class XnatSubject:
    def __init__(self, project_ID, subject_ID, interface):
        self.ID = subject_ID
        self.project = project_ID
        self.interface = interface
        self.uri = "'/REST/projects/%s/subjects/%s'"%(self.project, self.ID)

    def create(self):
        self.interface.execute_put("'/REST/projects/%s/subjects/%s'"%(self.project, self.ID))

    def delete(self, delete_files=False):
        if delete_files:
            self.interface.execute_delete(self.uri+'?removeFiles=true')
        self.interface.execute_delete(self.uri)

    def experiments(self):
        return [XnatExperiment(self.project, self.ID, experiment_ID, self.interface) for experiment_ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments?format=csv'"%(self.project, self.ID))]

    def experiment(self, experiment_ID):
        return XnatExperiment(self.project, self.ID, experiment_ID, self.interface)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects?format=csv'"%self.project)

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/subjects/%s/files/%s"%(self.project, self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/subjects/%s/files/%s"%(self.project, self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/files?format=csv'"%(self.project, self.ID))]

    def __repr__(self):
        return '<Subject "%s">'%(self.ID)

class XnatExperiment:
    def __init__(self, project_ID, subject_ID, experiment_ID, interface):
        self.ID = experiment_ID
        self.project = project_ID
        self.subject = subject_ID
        self.interface = interface
        self.uri = "'/REST/projects/%s/subjects/%s/experiments/%s'"%(self.project, self.subject, self.ID)

#    def create(self):
#        rest_cmd = "'/REST/projects/%s/subjects/%s/experiments[@xsi:type=xnat:mrSessionData]/%s"%(self.project, self.subject, self.ID)
##        rest_cmd += '?project=%s'%self.project
##        rest_cmd += '?ID=%s'%self.ID
##        rest_cmd += '?label=%s\''%self.ID
#        rest_cmd += "'"

#        print rest_cmd

#        self.interface.execute_put(rest_cmd)

    def delete(self, delete_files=False):
        if delete_files:
            self.interface.execute_delete(self.uri+'?removeFiles=true')
        self.interface.execute_delete(self.uri)

    def scans(self):
        return [XnatScan(self.project, self.subject, self.ID, scan_ID, self.interface) for scan_ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/scans?format=csv'"%(self.project, self.subject, self.ID), 1)]

    def scan(self, scan_ID):
        return XnatScan(self.project, self.subject, self.ID, scan_ID, self.interface)

    def reconstructions(self):
        return [XnatReconstruction(self.project, self.subject, self.ID, reconstruction_ID, self.interface) for reconstruction_ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/reconstructions?format=csv'"%(self.project, self.subject, self.ID), 1)]

    def reconstruction(self, reconstruction_ID):
        return XnatReconstruction(self.project, self.subject, self.ID, reconstruction_ID, self.interface)

    def assessors(self):
        return [XnatAssessor(self.project, self.subject, self.ID, assessor_ID, self.interface) for assessor_ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/assessors?format=csv'"%(self.project, self.subject, self.ID))]

    def assessor(self, assessor_ID):
        return XnatAssessor(self.project, self.subject, self.ID, assessor_ID, self.interface)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments?format=csv'"%(self.project, self.subject))

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/files/%s"%(self.project, self.subject, self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/files/%s"%(self.project, self.subject, self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/files?format=csv'"%(self.project, self.subject, self.ID))]

    def __repr__(self):
        return '<Experiment "%s">'%(self.ID)

class XnatScan:
    def __init__(self, project_ID, subject_ID, experiment_ID, scan_ID, interface):
        self.ID = scan_ID
        self.project = project_ID
        self.subject = subject_ID
        self.experiment = experiment_ID
        self.interface = interface
        self.uri = "'/REST/projects/%s/subjects/%s/experiments/%s/scans/%s'"%(self.project, self.subject, self.experiment, self.ID)

    def create(self):
        self.interface.execute_put("'/REST/projects/%s/subjects/%s/experiments/%s/scans/%s'"%(self.project, self.subject, self.experiment, self.ID))

    def delete(self, delete_files=False):
        if delete_files:
            self.interface.execute_delete(self.uri+'?removeFiles=true')
        self.interface.execute_delete(self.uri)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/scans?format=csv'"%(self.project, self.subject, self.experiment), 1)

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/scans/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/scans/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/scans/%s/files?format=csv'"%(self.project, self.subject, self.experiment, self.ID))]

    def __repr__(self):
        return '<Scan "%s">'%(self.ID)

class XnatReconstruction:
    def __init__(self, project_ID, subject_ID, experiment_ID, reconstruction_ID, interface):
        self.ID = reconstruction_ID
        self.project = project_ID
        self.subject = subject_ID
        self.experiment = experiment_ID
        self.interface = interface
        self.uri = "'/REST/projects/%s/subjects/%s/experiments/%s/reconstructions/%s'"%(self.project, self.subject, self.experiment, self.ID)

    def create(self):
        self.interface.execute_put("'/REST/projects/%s/subjects/%s/experiments/%s/reconstructions/%s'"%(self.project, self.subject, self.experiment, self.ID))

    def delete(self, delete_files=False):
        if delete_files:
            self.interface.execute_delete(self.uri+'?removeFiles=true')
        self.interface.execute_delete(self.uri)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/reconstructions?format=csv'"%(self.project, self.subject, self.experiment), 1)

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/reconstructions/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/reconstructions/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/reconstructions/%s/files?format=csv'"%(self.project, self.subject, self.experiment, self.ID))]

    def __repr__(self):
        return '<Reconstruction "%s">'%(self.ID)

class XnatAssessor:
    def __init__(self, project_ID, subject_ID, experiment_ID, assessor_ID, interface):
        self.ID = assessor_ID
        self.project = project_ID
        self.subject = subject_ID
        self.experiment = experiment_ID
        self.interface = interface
        self.uri = "'/REST/projects/%s/subjects/%s/experiments/%s/assessors/%s'"%(self.project, self.subject, self.experiment, self.ID)

#    def create(self):
#        self.interface.execute_put("'/REST/projects/%s/subjects/%s/experiments/%s/assessors/%s'"%(self.project, self.subject, self.experiment, self.ID))

    def delete(self, delete_files=False):
        if delete_files:
            self.interface.execute_delete(self.uri+'?removeFiles=true')
        self.interface.execute_delete(self.uri)

    def exists(self):
        return self.ID in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/assessors?format=csv'"%(self.project, self.subject, self.experiment))

    def file(self, file_name):
        return XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/assessors/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface)

    def files(self):
        return [XnatFile("/REST/projects/%s/subjects/%s/experiments/%s/assessors/%s/files/%s"%(self.project, self.subject, self.experiment, self.ID, file_name), self.interface) for file_name in self.interface.execute_get_csv("'/REST/projects/%s/subjects/%s/experiments/%s/assessors/%s/files?format=csv'"%(self.project, self.subject, self.experiment, self.ID))]

    def __repr__(self):
        return '<Assessor "%s">'%(self.ID)

class XnatFile:
    def __init__(self, uri, interface):
        self.ID = uri.split('/')[-1]
        self.uri = uri
        self.interface = interface

    def exists(self):
        return self.ID in self.interface.execute_get_csv('/'.join(self.uri.split('/')[:-1])+'?format=csv')

    def put(self, local_source):
        self.interface.execute_put("'%s' -local %s"%(self.uri, local_source))

    def get(self, local_destination=None):
        if local_destination is None:
            fd, local_destination = tempfile.mkstemp(suffix=self.ID)

        fd = open(local_destination, 'wb')
        fd.write(self.interface.execute_get("'%s'"%(self.uri)))
        fd.close()

        return local_destination        

#    def delete(self):
#        self.interface.execute_delete(self.uri+'?removeFiles=true')

    def __repr__(self):
        return '<File "%s">'%(self.ID)


if __name__ == '__main__':
    interface = XnatInterface('http://central.xnat.org:8080', 'mylogin', 'mypassword')

    #
    # most of the methods exists for all the classes. The main entry point is the XnatInterface class from which you can list and get XnatProjects.
    # XnatProjects can do the same for XnatSubjects and so on... here are the classes and their structure: 
    #
    # XnatInterface
    #   - XnatProject
    #       - XnatFile
    #       - XnatSubject
    #           - XnatFile
    #           - XnatExperiment
    #               - XnatFile
    #               - XnatScan
    #                   - XnatFile
    #               - XnatReconstruction
    #                   - XnatFile
    #               - XnatAssessor
    #                   - XnatFile
    #
    # note that XnatFiles can be uploaded/downloaded at every level be that may not be very relevant

    # the commented functions are work in progress...
    # normally you should be able to easily manage files from XNAT and browse XNAT types but at the moment I didn't provide any way to add metadata e.g. subject.age = 14
    # I didn't write any search method either because it would not be intuitive enough for now


    # returns the list of subjects
    interface.project('Volatile').subjects()
    
    # tests if the subject exists
    interface.project('Volatile').subject('060000126321').exists()

    # to get an experiment:
    interface.project('Volatile').subject('060000126321').experiment('SessionB_060000126321') 
    # OR
    XnatEperiment('Volatile', '060000126321', 'SessionB_060000126321', interface)

    # to upload a file:
    an_xnat_file = interface.project('Volatile').subject('060000126321').experiment('SessionB_060000126321').scan('test').file('image.nii.gz')
    an_xnat_file.exists() == False # because the file is not uploaded to the server, 'image.nii.gz' is the remote name of the file
    an_xnat_file.put('path_to_my_file_on_the_local_disk')

    # to download the file:
    # you can list the files
    interface.project('Volatile').subject('060000126321').experiment('SessionB_060000126321').scan('test').files()
    an_xnat_file = interface.project('Volatile').subject('060000126321').experiment('SessionB_060000126321').scan('test').file('image.nii.gz')
    an_xnat_file.exists() == True # because the file is on the server
    an_xnat_file.get() == '/tmp/857HJIimage.nii.gz' # downloads the file, returns the file path, the local destination path may be optionally specified


    # WARNING:
    # you must be careful, to upload a file to a scan, the scan element must have been created previously as well as all the ancestors
    # the 'create' method works but not all classes (like XnatExperiment) so you may have to create some initial structure through the web interface


