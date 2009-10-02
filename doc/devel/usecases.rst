===========
 Use Cases
===========

Below are some usecases written to demonstrate proposed APIs during
development.  **Note: These notes were taking during the Spring
of 2009.  This may not accurately represent the current design of the
software.**

Interface Convenience API
-------------------------

Eventually we will be using nipy image objects::

    img = ni.load_image('somefile.nii')
    template = ni.load_image('canonical.nii')

    flirter = ni.interfaces.Flirt()
    flirter.opts.searchcost='mutualinfo'
    newflirtimg, transform = ni.interfaces.register(fixed=template, 
                                                    moving=img,
                                                    interface=flirter)
    or
    newflirtimg,transform = ni.interfaces.register(fixed=template, moving=img, interface=ni.interfaces.Flirt())
    or
    spmcoreg = ni.interfaces.spm.Coregister()
    spmcoreg.opts.sep = [4,2]
    spmcoreg.opts.costfunction = 'mutual information'

    newspmimg, transform = ni.interfaces.register(fixed=template, moving=img, interface=spmcoreg)
    or
    newspmimg, transform = ni.interfaces.register(fixed=template, moving=img, interface=ni.interfaces.spm.Coregister())

**Non affine normalization**::

    wimg, warpfield = ni.interfaces.normalize(fixed=template, moving=img, interface=ni.interfaces.spm.Normalize())

    fslnormimg, warpfield =  ni.interfaces.normalize(fixed=template, moving=img, interface=ni.interfaces.Fnirt(affine=transform))


    gray, white, csf = ni.interfaces.segment(inimg=img, interface=spm.Segment())

Interfaces Basic
----------------

FLIRT
+++++

::

    flrt = fsl.Flirt()

    flrtd = flrt.run(infile='usrfile.nii',
                     reference='template.nii',
                     outfile='movedusr.nii', 
                     outmatrix='usr2template.mat')

    **or**

    flrt = fsl.Flirt(infile='usrfile.nii',
                     reference='template.nii',
                     outfile='movedusr.nii', 
                     outmatrix='usr2template.mat')
    flrtd2 = flrt.run()


    **just playing at cmd line**

    import nipy.interfaces.fsl as fsl

    flrtr = fsl.Flirt()
    flrtr.opts_help(opt)
    flrtr.opts.bins=640 
    flrtr.opts.searchcost='mutualinfo'
    newflrtr = flrtr.update(bins=256)
    flirted = newflrtr.run()

API into pipelining
-------------------

::

    import nipy.pipeline.node_wrapper as nw
    import nipy.pipeline.engine as pe
    import nipy.interfaces.fsl as fsl
    import nipy.interfaces.spm as spm


    datasource = nw.DataSource(interface=mydatasource(),
                               iterables=None,
                               output_directory='.')

    better = fsl.Bet(vertical_gradient=0.3)
    ssnode = nw.SkullStripNode(interface=better, 
                               iterables=dict(frac=lambda:[0.3,0.4,0.5]),
                               output_directory='.')

    coregnode - nw.CoregisterNode(interface=fsl.Flirt(), 
                                  iterables=None, 
                                  output_directory='.')


    normalize = spm.Normalize(template='/path/to/MNI152.nii')
    warpnode = nw.WarpNode(interface=normalize,
                           iterables=None,
                           output_directory='.')

    smoothnode = nw.SmoothNode(interface=spm.Smooth(),
                               iterables=dict(fwhm=lambda:[6,7,8]),
                               output_directory='.')



    pipeline1 = pe.Pipeline()
    pipeline1.addmodules([datasource,
                          ssnode,
                          coregnode,
                          warpnode,
                          smoothnode])

    pipeline1.connect([
                      (datasource,ssnode,[('anatomical','infile')]),
                      (ssnode,coregnode,[('outfile','source')]),
                      (datasource,ssnode,[('functional','infile')]),
                      (ssnode,coregnode,[('outfile','moving')]),
                      (coregnode,warpnode,[('outfile','source')]),
                      (warpnode, smoothnode,[('outfile', 'infile')])
                      ])
    pipeline1.run()


**Pipeline Nodes**
SkullStripNode
CoregisterNode
CoregisterTransformOnlyNode
ApplyTransformNode
ResliceNode
RealignNode
SmoothNode
WarpNode
ArtifactDetectNode

**check these for use across (fsl, spm, nipy)**

ModelSpecificationNode
ModelDesignNode
ModelEstimateNode
ContrastEstimateNode



..Note:

    Main questions:

    when call .run()
    should the attributes set with a run call be properties?

    too many objects

     property that doesnt replace gettr settr just doc

