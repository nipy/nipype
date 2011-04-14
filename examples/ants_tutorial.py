import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.ants as ants
import nibabel as nb
import os                                    # system functions

data_dir = os.path.abspath('antsdata/brains')
subject_list = ['B1', 'B2', 'B3', 'B4' ,'B5']

#data_dir = os.path.abspath('antsdata/faces')
#subject_list = ['YFace1', 'YFace2', 'YFace3', 'YFace4', 'YFace5','YFace6', 'YFace7', 'YFace8', 'YFace9']

"""
Use infosource node to loop through the subject list and define the input files.
"""

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(images=[['subject_id']])

"""
Use datasource node to perform the actual data grabbing.
Templates for the associated images are used to obtain the correct images.
"""
datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s"
datasource.inputs.base_directory = data_dir
datasource.inputs.field_template = dict(images='%s.tiff')
datasource.inputs.template_args = info
datasource.inputs.base_directory = data_dir


inputnode = pe.Node(interface=util.IdentityInterface(fields=['subject_id','images']), name='inputnode')


#${ANTSPATH}AverageImages $DIM ${TEMPLATE} 0 $IMAGESETVARIABLE
#ConvertToJpg template.nii template0.jpg


    #${ANTSPATH}ANTS $DIM -m  $LOCALMETRIC  -t $TRANSFORMATION  -r $REGULARIZATION -o ${NAMING}   -i $ITERATIONS
#  LOCALMETRIC=${METRIC},$x,${METRICPARAMS}
#  TRANSFORMATION=SyN[1]
#  REGULARIZATION=Gauss[3,1]
#  METRICPARAMS=1,4,-0.95]
createTemplate = pe.MapNode(interface=ants.ANTS_Probabilistic(), name='createTemplate',
    iterfield = 'moving_images')
#createTemplate.inputs.image_metric = 'CC'
createTemplate.inputs.weight = 0
createTemplate.inputs.radius = 0.5

createTemplate.inputs.transformation_model = 'SyN'
createTemplate.inputs.transformation_gradient_step_length = 2
#createTemplate.inputs.transformation_delta_time = 2
#createTemplate.inputs.transformation_number_of_time_steps = 100

createTemplate.inputs.regularization = 'Gauss'
createTemplate.inputs.regularization_gradient_field_sigma = 3
createTemplate.inputs.regularization_deformation_field_sigma = 0.5
#createTemplate.inputs.regularization_truncation = 0
createTemplate.inputs.iterations = [50, 50, 10]
createTemplate.inputs.image_dimension = 2
createTemplate.inputs.fixed_image = data_dir + '/B1.tiff'
createTemplate.inputs.out_file = 'erikoutputtest.tiff'

   # ${ANTSPATH}WarpImageMultiTransform $DIM  $x    ${NAMING}registered.nii ${NAMING}Warp.nii ${NAMING}Affine.txt  -R ${TEMPLATE}

warpToTemplate = pe.Node(interface=ants.MeasureImageSimilarity(), name='warpToTemplate')
#Connect template to reference image

  #  ${ANTSPATH}MeasureImageSimilarity $DIM 2 ${TEMPLATE} ${NAMING}registered.nii ${TEMPLATENAME}metriclog.txt

imageSimilarity = pe.Node(interface=ants.MeasureImageSimilarity(), name='imageSimilarity')
imageSimilarity.inputs.image_metric = '2' #2-Mutual Information

 #   ${ANTSPATH}AverageImages $DIM ${TEMPLATE} 1 ${OUTPUTNAME}*registered.nii

averageTemplate = pe.Node(interface=ants.AverageImages(), name='averageX')
averageTemplate.inputs.normalize = True

averageX = pe.Node(interface=ants.AverageImages(), name='averageX')
averageX.inputs.normalize = False
averageY = averageX.clone('averageY')
averageZ = averageX.clone('averageZ')

multiplyX = pe.Node(interface=ants.MultiplyImages(), name='multiplyX')
multiplyY = multiplyX.clone('multiplyY')
multiplyZ = multiplyX.clone('multiplyZ')

#   ${ANTSPATH}MultiplyImages  $DIM ${TEMPLATENAME}warpxvec.nii -0.15 ${TEMPLATENAME}warpxvec.nii
#    ${ANTSPATH}MultiplyImages  $DIM ${TEMPLATENAME}warpyvec.nii -0.15  ${TEMPLATENAME}warpyvec.nii

#   ${ANTSPATH}WarpImageMultiTransform $DIM  ${TEMPLATE}   ${TEMPLATE} ${TEMPLATENAME}warp.nii ${TEMPLATENAME}warp.nii ${TEMPLATENAME}warp.nii  ${TEMPLATENAME}warp.nii  -R ${TEMPLATE}
#    ${ANTSPATH}MeasureMinMaxMean $DIM ${TEMPLATENAME}warpxvec.nii  ${TEMPLATENAME}warpxlog.txt  1
#    ${ANTSPATH}MeasureMinMaxMean $DIM ${TEMPLATENAME}warpyvec.nii  ${TEMPLATENAME}warpylog.txt  1

"""
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial can is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""
normalize = pe.Workflow(name="normalize")
normalize.connect([(inputnode, createTemplate,[('images','moving_images')])])

ants = pe.Workflow(name="ants_tutorial")
ants.base_dir = os.path.abspath('ants_tutorial')
ants.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,normalize,[('images','inputnode.images')]),
                    (infosource,normalize,[('subject_id','inputnode.subject_id')]),
                ])

ants.run()
ants.write_graph()

"""
This outputted .dot graph can be converted to a vector image for use in figures via the following command-line function:
dot -Tps graph.dot > graph.eps
"""
