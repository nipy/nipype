import os
import nipype
from nipype.interfaces.utility import Function,IdentityInterface
import nipype.pipeline.engine as pe  # pypeline engine
from nipype.interfaces.freesurfer import *
from nipype.interfaces.io import DataGrabber
from nipype.interfaces.utility import Merge

def create_ba_maps_wf(name="Brodmann_Area_Maps", th3=True):
    # Brodmann Area Maps (BA Maps) and Hinds V1 Atlas
    inputs = ['lh_sphere_reg',
              'rh_sphere_reg',
              'lh_white',
              'rh_white',
              'lh_pial',
              'rh_pial',
              'lh_orig',
              'rh_orig',
              'transform',
              'lh_thickness',
              'rh_thickness',
              'brainmask',
              'aseg',
              'ribbon',
              'wm',
              'src_subject_id',
              'src_subject_dir',
              'color_table']
    
    inputspec = pe.Node(IdentityInterface(fields=inputs),
                        name="inputspec")

    ba_WF = pe.Workflow(name=name)
        
    outputSpec = pe.Node(IdentityInterface(fields=['lh_table',
                                                   'lh_color',
                                                   'lh_thresh_table',
                                                   'lh_thresh_color',
                                                   'rh_table',
                                                   'rh_color',
                                                   'rh_thresh_table',
                                                   'rh_thresh_color']),
                         name="outputspec")

    labels = ["BA1", "BA2", "BA3a", "BA3b", "BA4a", "BA4p", "BA6",
              "BA44", "BA45", "V1", "V2", "MT", "entorhinal", "perirhinal"]
    for hemisphere in ['lh', 'rh']:
        for threshold in [True, False]:
            field_template = dict(sphere_reg='surf/{0}.sphere.reg'.format(hemisphere),
                                  white='surf/{0}.white'.format(hemisphere))

            out_files = list()
            if threshold:
                for label in labels:
                    out_file = '{0}.{1}_exvivo.thresh.label'.format(hemisphere, label)
                    out_files.append(out_file)
                    field_template[label] = 'label/' + out_file
                node_name = 'BA_Maps_' + hemisphere + '_Tresh'
            else:
                for label in labels:
                    out_file = '{0}.{1}_exvivo.label'.format(hemisphere, label)
                    out_files.append(out_file)
                    field_template[label] = 'label/' + out_file
                node_name = 'BA_Maps_' + hemisphere

            source_fields = labels + ['sphere_reg', 'white']
            source_subject = pe.Node(DataGrabber(outfields=source_fields),
                                     name=node_name + "_srcsubject")
            source_subject.inputs.template = '*'
            source_subject.inputs.sort_filelist = False
            source_subject.inputs.field_template = field_template
            ba_WF.connect([(inputspec, source_subject, [('src_subject_dir', 'base_directory')])])
            
            merge_labels = pe.Node(Merge(len(labels)),
                                   name=node_name + "_Merge")
            for i,label in enumerate(labels):
                ba_WF.connect([(source_subject, merge_labels, [(label, 'in{0}'.format(i+1))])])

            node = pe.MapNode(Label2Label(), name=node_name,
                              iterfield=['source_label', 'out_file'])
            node.inputs.hemisphere = hemisphere
            node.inputs.out_file = out_files
            node.inputs.copy_inputs = True
            
            ba_WF.connect([(merge_labels, node, [('out', 'source_label')]),
                           (source_subject, node, [('sphere_reg', 'source_sphere_reg'),
                                                   ('white', 'source_white')]),
                           (inputspec, node, [('src_subject_id', 'source_subject')])])
            
            label2annot = pe.Node(Label2Annot(), name=node_name + '_2_Annot')
            label2annot.inputs.hemisphere = hemisphere
            label2annot.inputs.verbose_off = True
            label2annot.inputs.keep_max = True
            label2annot.inputs.copy_inputs = True

            stats_node = pe.Node(ParcellationStats(), name=node_name + '_Stats')
            stats_node.inputs.hemisphere = hemisphere
            stats_node.inputs.mgz = True
            stats_node.inputs.th3 = th3
            stats_node.inputs.surface = 'white'
            stats_node.inputs.tabular_output = True
            stats_node.inputs.copy_inputs = True

            if threshold:
                label2annot.inputs.out_annot = "BA_exvivo.thresh"
                ba_WF.connect([(stats_node, outputSpec, [('out_color', 
                                                          '{0}_thresh_color'.format(hemisphere)),
                                                         ('out_table', 
                                                          '{0}_thresh_table'.format(hemisphere))])])
            else:
                label2annot.inputs.out_annot = "BA_exvivo"
                ba_WF.connect([(stats_node, outputSpec, [('out_color', 
                                                          '{0}_color'.format(hemisphere)),
                                                         ('out_table', 
                                                          '{0}_table'.format(hemisphere))])])


            ba_WF.connect([(inputspec, node, [('{0}_sphere_reg'.format(hemisphere),
                                               'sphere_reg'),
                                              ('{0}_white'.format(hemisphere), 'white'),
                                              ]),
                           (node, label2annot, [('out_file', 'in_labels')]),
                           (inputspec, label2annot, [('{0}_orig'.format(hemisphere), 'orig'),
                                                     ('color_table', 'color_table')]),
                           (label2annot, stats_node,
                            [('out_file', 'in_annotation')]),
                           (inputspec, stats_node, [('{0}_thickness'.format(hemisphere), 
                                                     'thickness'),
                                                    ('lh_white', 'lh_white'),
                                                    ('rh_white', 'rh_white'),
                                                    ('lh_pial', 'lh_pial'),
                                                    ('rh_pial', 'rh_pial'),
                                                    ('transform', 'transform'),
                                                    ('brainmask', 'brainmask'),
                                                    ('aseg', 'aseg'),
                                                    ('wm', 'wm'),
                                                    ('ribbon', 'ribbon')])])


    return ba_WF
