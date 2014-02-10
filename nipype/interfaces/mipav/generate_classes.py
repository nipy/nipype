from nipype.interfaces.slicer.generate_classes import generate_all_classes


if __name__ == "__main__":
    ## NOTE:  For now either the launcher needs to be found on the default path, or
    ##        every tool in the modules list must be found on the default path
    ##        AND calling the module with --xml must be supported and compliant.
    modules_list = ['edu.jhu.bme.smile.demo.RandomVol']

    ## SlicerExecutionModel compliant tools that are usually statically built, and don't need the Slicer3 --launcher
    generate_all_classes(modules_list=modules_list,launcher=["java edu.jhu.ece.iacl.jist.cli.run" ])
    ## Tools compliant with SlicerExecutionModel called from the Slicer environment (for shared lib compatibility)
    #launcher = ['/home/raid3/gorgolewski/software/slicer/Slicer', '--launch']
    #generate_all_classes(modules_list=modules_list, launcher=launcher)
    #generate_all_classes(modules_list=['BRAINSABC'], launcher=[] )])
    ## Tools compliant with SlicerExecutionModel called from the Slicer environment (for shared lib compatibility)
    #launcher = ['/home/raid3/gorgolewski/software/slicer/Slicer', '--launch']
    #generate_all_classes(modules_list=modules_list, launcher=launcher)
    #generate_all_classes(modules_list=['BRAINSABC'], launcher=[] )