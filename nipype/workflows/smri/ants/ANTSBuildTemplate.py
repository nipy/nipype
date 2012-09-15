#################################################################################
## Program:   Build Template Parallel
## Language:  Python
##
## Authors:  Jessica Forbes, Grace Murray, and Hans Johnson, University of Iowa
##
##      This software is distributed WITHOUT ANY WARRANTY; without even
##      the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
##      PURPOSE.
##
#################################################################################

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
from nipype.interfaces.io import DataGrabber
from nipype.interfaces.utility import Merge, Split, Function, Rename, IdentityInterface

from nipype.interfaces.ants import AverageImages, AverageAffineTransform, MultiplyImages, ANTS, WarpImageMultiTransform

def GetFirstListElement(this_list):
    return this_list[0]

def MakeTransformListWithGradientWarps(averageAffineTranform, gradientStepWarp):
    return [averageAffineTranform, gradientStepWarp, gradientStepWarp, gradientStepWarp, gradientStepWarp]
def RenestDeformedPassiveImages(deformedPassiveImages,flattened_image_nametypes):
    import os
    """ Now make a list of lists of images where the outter list is per image type,
    and the inner list is the same size as the number of subjects to be averaged.
    In this case, the first element will be a list of all the deformed T2's, and
    the second element will be a list of all deformed POSTERIOR_AIR,  etc..
    """
    all_images_size=len(deformedPassiveImages)
    image_dictionary_of_lists=dict()
    nested_imagetype_list=list()
    outputAverageImageName_list=list()
    image_type_list=list()
    ## make empty_list, this is not efficient, but it works
    for name in flattened_image_nametypes:
        image_dictionary_of_lists[name]=list()
    for index in range(0,all_images_size):
        curr_name=flattened_image_nametypes[index]
        curr_file=deformedPassiveImages[index]
        image_dictionary_of_lists[curr_name].append(curr_file)
    for image_type,image_list in image_dictionary_of_lists.items():
        nested_imagetype_list.append(image_list)
        outputAverageImageName_list.append('AVG_'+image_type+'.nii.gz')
        image_type_list.append('WARP_AVG_'+image_type)
    print "\n"*10
    print "HACK: ", nested_imagetype_list
    print "HACK: ", outputAverageImageName_list
    print "HACK: ", image_type_list
    return nested_imagetype_list,outputAverageImageName_list,image_type_list

## Utility Function
## This will make a list of list pairs for defining the concatenation of transforms
## wp=['wp1.nii','wp2.nii','wp3.nii']
## af=['af1.mat','af2.mat','af3.mat']
## ll=map(list,zip(af,wp))
## ll
##[['af1.mat', 'wp1.nii'], ['af2.mat', 'wp2.nii'], ['af3.mat', 'wp3.nii']]
def MakeListsOfTransformLists(warpTransformList, AffineTransformList):
    return map(list, zip(warpTransformList,AffineTransformList))

## Flatten and return equal length transform and images lists.
def FlattenTransformAndImagesList(ListOfPassiveImagesDictionararies,transformation_series):
    import sys
    print("HACK:  DEBUG: ListOfPassiveImagesDictionararies\n{lpi}\n".format(lpi=ListOfPassiveImagesDictionararies))
    subjCount=len(ListOfPassiveImagesDictionararies)
    tranCount=len(transformation_series)
    if subjCount != tranCount:
        print "ERROR:  subjCount must equal tranCount {0} != {1}".format(subjCount,tranCount)
        sys.exit(-1)
    flattened_images=list()
    flattened_image_nametypes=list()
    flattened_transforms=list()
    passiveImagesCount = len(ListOfPassiveImagesDictionararies[0])
    for subjIndex in range(0,subjCount):
        #if passiveImagesCount != len(ListOfPassiveImagesDictionararies[subjIndex]):
        #    print "ERROR:  all image lengths must be equal {0} != {1}".format(passiveImagesCount,len(ListOfPassiveImagesDictionararies[subjIndex]))
        #    sys.exit(-1)
        subjImgDictionary=ListOfPassiveImagesDictionararies[subjIndex]
        subjToAtlasTransform=transformation_series[subjIndex]
        for imgname,img in subjImgDictionary.items():
            flattened_images.append(img)
            flattened_image_nametypes.append(imgname)
            flattened_transforms.append(subjToAtlasTransform)
    print("HACK: flattened images    {0}\n".format(flattened_images))
    print("HACK: flattened nametypes {0}\n".format(flattened_image_nametypes))
    print("HACK: flattened txfms     {0}\n".format(flattened_transforms))
    return flattened_images,flattened_transforms,flattened_image_nametypes
##
## NOTE:  The modes can be either 'SINGLE_IMAGE' or 'MULTI'
##        'SINGLE_IMAGE' is quick shorthand when you are building an atlas with a single subject, then registration can
##                    be short-circuted
##        any other string indicates the normal mode that you would expect and replicates the shell script build_template_parallel.sh
def ANTSTemplateBuildSingleIterationWF(iterationPhasePrefix,CLUSTER_QUEUE,mode='MULTI'):

    TemplateBuildSingleIterationWF = pe.Workflow(name = 'ANTSTemplateBuildSingleIterationWF_'+iterationPhasePrefix)

    inputSpec = pe.Node(interface=util.IdentityInterface(fields=['images', 'fixed_image',
                'ListOfPassiveImagesDictionararies']),
                run_without_submitting=True,
                name='InputSpec')
    ## HACK: TODO: Need to move all local functions to a common untility file, or at the top of the file so that
    ##             they do not change due to re-indenting.  Otherwise re-indenting for flow control will trigger
    ##             their hash to change.
    ## HACK: TODO: REMOVE 'transforms_list' it is not used.  That will change all the hashes
    ## HACK: TODO: Need to run all python files through the code beutifiers.  It has gotten pretty ugly.
    outputSpec = pe.Node(interface=util.IdentityInterface(fields=['template','transforms_list',
                'passive_deformed_templates']),
                run_without_submitting=True,
                name='OutputSpec')

    if mode == 'SINGLE_IMAGEXX':
        ### HACK:  A more general utility that is reused should be created.
        print "HACK: DOING SINGLE_IMAGE ", mode
        TemplateBuildSingleIterationWF.connect( [ (inputSpec, outputSpec, [(('images', GetFirstListElement ), 'template')] ), ])
        ##HACK THIS DOES NOT WORK BECAUSE FILE NAMES ARE WRONG.
        TemplateBuildSingleIterationWF.connect( [ (inputSpec, outputSpec, [(('ListOfPassiveImagesDictionararies', GetFirstListElement ), 'passive_deformed_templates')] ), ])
        return TemplateBuildSingleIterationWF

    print "HACK: DOING MULTI_IMAGE ", mode
    ##import sys
    ##sys.exit(-1)



    ### NOTE MAP NODE! warp each of the original images to the provided fixed_image as the template
    BeginANTS=pe.MapNode(interface=ANTS(), name = 'BeginANTS', iterfield=['moving_image'])
    many_cpu_BeginANTS_options_dictionary={'qsub_args': '-S /bin/bash -pe smp1 8-12 -l mem_free=6000M -o /dev/null -e /dev/null '+CLUSTER_QUEUE, 'overwrite': True}
    BeginANTS.plugin_args=many_cpu_BeginANTS_options_dictionary
    BeginANTS.inputs.dimension = 3
    BeginANTS.inputs.output_transform_prefix = iterationPhasePrefix+'_tfm'
    BeginANTS.inputs.metric = ['CC']
    BeginANTS.inputs.metric_weight = [1.0]
    BeginANTS.inputs.radius = [5]
    BeginANTS.inputs.transformation_model = 'SyN'
    BeginANTS.inputs.gradient_step_length = 0.25
    if mode == 'SINGLE_IMAGE_IMAGE':
        ## HACK:  Just short circuit time consuming step if only registering a single image.
        BeginANTS.inputs.number_of_iterations = [1]
        BeginANTS.inputs.number_of_affine_iterations = [1]
    else:
        BeginANTS.inputs.number_of_iterations = [50, 35, 15]
        BeginANTS.inputs.number_of_affine_iterations = [10000,10000,10000,10000,10000]
    BeginANTS.inputs.use_histogram_matching = True
    BeginANTS.inputs.mi_option = [32, 16000]
    BeginANTS.inputs.regularization = 'Gauss'
    BeginANTS.inputs.regularization_gradient_field_sigma = 3
    BeginANTS.inputs.regularization_deformation_field_sigma = 0
    TemplateBuildSingleIterationWF.connect(inputSpec, 'images', BeginANTS, 'moving_image')
    TemplateBuildSingleIterationWF.connect(inputSpec, 'fixed_image', BeginANTS, 'fixed_image')

    MakeTransformsLists = pe.Node(interface=util.Function(function=MakeListsOfTransformLists,
                    input_names=['warpTransformList', 'AffineTransformList'],
                    output_names=['out']),
                    run_without_submitting=True,
                    name='MakeTransformsLists')
    MakeTransformsLists.inputs.ignore_exception = True
    TemplateBuildSingleIterationWF.connect(BeginANTS, 'warp_transform', MakeTransformsLists, 'warpTransformList')
    TemplateBuildSingleIterationWF.connect(BeginANTS, 'affine_transform', MakeTransformsLists, 'AffineTransformList')

    ## Now warp all the moving_images images
    wimtdeformed = pe.MapNode(interface = WarpImageMultiTransform(),
                     iterfield=['transformation_series', 'moving_image'],
                     name ='wimtdeformed')
    TemplateBuildSingleIterationWF.connect(inputSpec, 'images', wimtdeformed, 'moving_image')
    TemplateBuildSingleIterationWF.connect(MakeTransformsLists, 'out', wimtdeformed, 'transformation_series')


    ##  Shape Update Next =====
    ## Now  Average All moving_images deformed images together to create an updated template average
    AvgDeformedImages=pe.Node(interface=AverageImages(), name='AvgDeformedImages')
    AvgDeformedImages.inputs.dimension = 3
    AvgDeformedImages.inputs.output_average_image = iterationPhasePrefix+'.nii.gz'
    AvgDeformedImages.inputs.normalize = 1
    TemplateBuildSingleIterationWF.connect(wimtdeformed, "output_image", AvgDeformedImages, 'images')

    ## Now average all affine transforms together
    AvgAffineTransform = pe.Node(interface=AntsAverageAffineTransform(), name = 'AvgAffineTransform')
    AvgAffineTransform.inputs.dimension = 3
    AvgAffineTransform.inputs.output_affine_transform = iterationPhasePrefix+'Affine.mat'
    TemplateBuildSingleIterationWF.connect(BeginANTS, 'affine_transform', AvgAffineTransform, 'transforms')

    ## Now average the warp fields togther
    AvgWarpImages=pe.Node(interface=AverageImages(), name='AvgWarpImages')
    AvgWarpImages.inputs.dimension = 3
    AvgWarpImages.inputs.output_average_image = iterationPhasePrefix+'warp.nii.gz'
    AvgWarpImages.inputs.normalize = 1
    TemplateBuildSingleIterationWF.connect(BeginANTS, 'warp_transform', AvgWarpImages, 'images')

    ## Now average the images together
    ## TODO:  For now GradientStep is set to 0.25 as a hard coded default value.
    GradientStep = 0.25
    GradientStepWarpImage=pe.Node(interface=MultiplyImages(), name='GradientStepWarpImage')
    GradientStepWarpImage.inputs.dimension = 3
    GradientStepWarpImage.inputs.second_input = -1.0 * GradientStep
    GradientStepWarpImage.inputs.output_product_image = iterationPhasePrefix+'warp.nii.gz'
    TemplateBuildSingleIterationWF.connect(AvgWarpImages, 'average_image', GradientStepWarpImage, 'first_input')

    ## Now create the new template shape based on the average of all deformed images
    UpdateTemplateShape = pe.Node(interface = WarpImageMultiTransform(), name = 'UpdateTemplateShape')
    UpdateTemplateShape.inputs.invert_affine = [1]
    TemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', UpdateTemplateShape, 'reference_image')
    TemplateBuildSingleIterationWF.connect(AvgAffineTransform, 'affine_transform', UpdateTemplateShape, 'transformation_series')
    TemplateBuildSingleIterationWF.connect(GradientStepWarpImage, 'product_image', UpdateTemplateShape, 'moving_image')

    ApplyInvAverageAndFourTimesGradientStepWarpImage = pe.Node(interface=util.Function(function=MakeTransformListWithGradientWarps,
                                         input_names=['averageAffineTranform', 'gradientStepWarp'],
                                         output_names=['TransformListWithGradientWarps']),
                 run_without_submitting=True,
                 name='MakeTransformListWithGradientWarps')
    ApplyInvAverageAndFourTimesGradientStepWarpImage.inputs.ignore_exception = True

    TemplateBuildSingleIterationWF.connect(AvgAffineTransform, 'affine_transform', ApplyInvAverageAndFourTimesGradientStepWarpImage, 'averageAffineTranform')
    TemplateBuildSingleIterationWF.connect(UpdateTemplateShape, 'output_image', ApplyInvAverageAndFourTimesGradientStepWarpImage, 'gradientStepWarp')

    ReshapeAverageImageWithShapeUpdate = pe.Node(interface = WarpImageMultiTransform(), name = 'ReshapeAverageImageWithShapeUpdate')
    ReshapeAverageImageWithShapeUpdate.inputs.invert_affine = [1]
    ReshapeAverageImageWithShapeUpdate.inputs.out_postfix = '_Reshaped'
    TemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', ReshapeAverageImageWithShapeUpdate, 'moving_image')
    TemplateBuildSingleIterationWF.connect(AvgDeformedImages, 'average_image', ReshapeAverageImageWithShapeUpdate, 'reference_image')
    TemplateBuildSingleIterationWF.connect(ApplyInvAverageAndFourTimesGradientStepWarpImage, 'TransformListWithGradientWarps', ReshapeAverageImageWithShapeUpdate, 'transformation_series')
    TemplateBuildSingleIterationWF.connect(ReshapeAverageImageWithShapeUpdate, 'output_image', outputSpec, 'template')

    ######
    ######
    ######  Process all the passive deformed images in a way similar to the main image used for registration
    ######
    ######
    ######
    ##############################################
    ## Now warp all the ListOfPassiveImagesDictionararies images
    FlattenTransformAndImagesListNode = pe.Node( Function(function=FlattenTransformAndImagesList,
                                  input_names = ['ListOfPassiveImagesDictionararies','transformation_series'],
                                  output_names = ['flattened_images','flattened_transforms','flattened_image_nametypes']),
                                  run_without_submitting=True, name="99_FlattenTransformAndImagesList")
    TemplateBuildSingleIterationWF.connect( inputSpec,'ListOfPassiveImagesDictionararies', FlattenTransformAndImagesListNode, 'ListOfPassiveImagesDictionararies' )
    TemplateBuildSingleIterationWF.connect( MakeTransformsLists ,'out', FlattenTransformAndImagesListNode, 'transformation_series' )
    wimtPassivedeformed = pe.MapNode(interface = WarpImageMultiTransform(),
                     iterfield=['transformation_series', 'moving_image'],
                     name ='wimtPassivedeformed')
    TemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_images',     wimtPassivedeformed, 'moving_image')
    TemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_transforms', wimtPassivedeformed, 'transformation_series')

    RenestDeformedPassiveImagesNode = pe.Node( Function(function=RenestDeformedPassiveImages,
                                  input_names = ['deformedPassiveImages','flattened_image_nametypes'],
                                  output_names = ['nested_imagetype_list','outputAverageImageName_list','image_type_list']),
                                  run_without_submitting=True, name="99_RenestDeformedPassiveImages")
    TemplateBuildSingleIterationWF.connect(wimtPassivedeformed, 'output_image', RenestDeformedPassiveImagesNode, 'deformedPassiveImages')
    TemplateBuildSingleIterationWF.connect(FlattenTransformAndImagesListNode, 'flattened_image_nametypes', RenestDeformedPassiveImagesNode, 'flattened_image_nametypes')
    ## Now  Average All passive moving_images deformed images together to create an updated template average
    AvgDeformedPassiveImages=pe.MapNode(interface=AverageImages(),
      iterfield=['images','output_average_image'],
      name='AvgDeformedPassiveImages')
    AvgDeformedPassiveImages.inputs.dimension = 3
    AvgDeformedPassiveImages.inputs.normalize = 0
    TemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "nested_imagetype_list", AvgDeformedPassiveImages, 'images')
    TemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "outputAverageImageName_list", AvgDeformedPassiveImages, 'output_average_image')

    ## -- TODO:  Now neeed to reshape all the passive images as well
    ReshapeAveragePassiveImageWithShapeUpdate = pe.MapNode(interface = WarpImageMultiTransform(),
      iterfield=['moving_image','reference_image','out_postfix'],
      name = 'ReshapeAveragePassiveImageWithShapeUpdate')
    ReshapeAveragePassiveImageWithShapeUpdate.inputs.invert_affine = [1]
    TemplateBuildSingleIterationWF.connect(RenestDeformedPassiveImagesNode, "image_type_list", ReshapeAveragePassiveImageWithShapeUpdate, 'out_postfix')
    TemplateBuildSingleIterationWF.connect(AvgDeformedPassiveImages, 'average_image', ReshapeAveragePassiveImageWithShapeUpdate, 'moving_image')
    TemplateBuildSingleIterationWF.connect(AvgDeformedPassiveImages, 'average_image', ReshapeAveragePassiveImageWithShapeUpdate, 'reference_image')
    TemplateBuildSingleIterationWF.connect(ApplyInvAverageAndFourTimesGradientStepWarpImage, 'TransformListWithGradientWarps', ReshapeAveragePassiveImageWithShapeUpdate, 'transformation_series')
    TemplateBuildSingleIterationWF.connect(ReshapeAveragePassiveImageWithShapeUpdate, 'output_image', outputSpec, 'passive_deformed_templates')

    return TemplateBuildSingleIterationWF
