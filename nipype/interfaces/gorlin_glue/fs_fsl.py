#!/usr/bin/python
#coding:utf-8

"""Functions for integrating Freesurfer and FSL"""
import freesurfer
import fsl
import os
import glob
import shutil
p=os.path
def feat2standard(feat, targsubject=None, gfeat=False, copes=True, onlyUpdate=True):
    """Projects a feat dir through the cortical surface into 3D space
    
    :Parameters:
      feat: directory.  Must contain a reg/freesurfer folder
      targsubject: If None, is subject's.  Otherwise resamples
    """
    reg = p.join(feat, 'reg', 'freesurfer', 'anat2exf.register.dat')
        
    if not p.isfile(reg):
        raise RuntimeError('No registration file!')
    if targsubject is None:
        sname='highres'
        f = open(reg)
        targsubject=f.readline().strip()
        f.close()
    else:
        sname=targsubject
    brain = p.join(freesurfer.SUBJECTS_DIR, targsubject, 'mri', 'brain.mgz')
    #if not p.isfile(brain+'.nii.gz'):
        #freesurfer.call('mri_convert %s.mgz %.nii.gz'%(brain, brain))
    #brain += '.nii.gz'
    outdir = p.join(feat, '%s.feat'%sname)
    if not p.isdir(outdir):
        os.makedirs(outdir)
    designs = glob.glob(p.join(feat, 'design.*'))
    for d in designs:
        shutil.copy(d, outdir)
    templh=p.join(feat, 'tmplhsurf.mgz')
    temprh=p.join(feat, 'tmprhsurf.mgz')
    if p.isfile(templh):
        os.remove(templh)
    if p.isfile(temprh):
        os.remove(temprh)
        
    files = ['bg_image', 'mask', 'mean_func']
    if copes:
        files.extend(['stats/cope*', 'stats/varcope*'])
    
    template = freesurfer.SUBJECTS_DIR
    for f in files:
        (subdir, junk) = p.split(f)
        matches = fsl.imglob(p.join(feat, f), strip=False, first=False)
        if not isinstance(matches, list):
            if not matches:
                continue
            matches=[matches]
        try:
            os.makedirs(p.join(outdir, subdir))
        except Exception:
            pass
        for im in matches:
            (junk, imname) = p.split(im)
            outim = p.join(outdir, subdir, imname)
            if not (onlyUpdate or p.isfile(outim)):
                v2s = 'mri_vol2surf --mov %s --reg %s'%(im, reg)
                if not targsubject is None:
                    v2s += ' --trgsubject ' + targsubject
                v2s += ' --projfrac-avg 0 1 .1'
                #v2s += ' --out ' + tempsurf
                freesurfer.call(v2s + ' --hemi lh --out '+templh)
                freesurfer.call(v2s + ' --hemi rh --out '+temprh)
                s2v = 'mri_surf2vol --fillribbon'
                s2v += ' --identity %s --template %s'%(targsubject, brain)
                lo = p.join(outdir, subdir, 'lh.'+imname) 
                ro = p.join(outdir, subdir, 'rh.'+imname)
                freesurfer.call(s2v + ' --hemi lh --o %s --surfval %s'%(lo, templh))
                freesurfer.call(s2v + ' --hemi rh --o %s --surfval %s'%(ro, temprh))
                fsl.call('fslmaths %s -max %s %s'%(lo, ro, outim))
                os.remove(lo)
                os.remove(ro)
                os.remove(templh)
                os.remove(temprh)
    fsl.junk_reg_standard(outdir)
    if not len(fsl.imglob(p.join(outdir, 'bg_image'))):
        freesurfer.call('mri_convert %s %s'%(p.join(freesurfer.SUBJECTS_DIR, targsubject, 'mri', 'brain.mgz'),
                                             p.join(outdir, 'bg_image.nii.gz')))
    
def feat2surf(feat, reg=None, subject=None, targsubject=None, fwhm=None,
              gfeat=False, convertOut=True, convertAsync=False, runAll=False,
              zstats=False, zfstats=False, projectCopes=True, update=False,
              preClear=False):
    """Projects a feat directory onto a subjects surface
    
    Unlike Freesurfer's feat2surf, this takes a single .{g}feat directory
    as input, projects each subcope directory's cope and varcopes.  It creates
    as output two directories in the .gfeat: lh{_targsubj}.gfeat and rh
    
    Enough copes and varcopes are copied/projected from the original gfeat and
    cope directories that you can directly run a higher-level feat on each cope
    directory
    
    :targsubject:
    after sampling onto the subject, if not None, the data is resampled onto 
    this subject's surface (using spherical surface registration).  Most common
    option is probably 'fsaverage'.  Defaults to 'fsaverage' if gfeat is True.
    
    :reg:
    A path to a freesurfer registration file (ie register.dat)
    If None, then it will use {feat}/reg/freesurfer/anat2exf.register.dat
    OR if this file does not exist, then identity is assumed (i.e. files are
    already in anatomical space), but this requires the subject argument
    
    :subject:
    the FS subject to map the anatomy onto, if already sampled into anatomical
    space, and no reg file is provided
    
    :gfeat:
    If the target directory is a gfeat, then each cope directory is projected
    If False, then this treats the directory as a first-level analysis and 
    copies the files into two new 'first level' directories, putting the
    results into 'reg_standard' folders for inclusion in higher-level gfeats
    
    :runAll:
    If True, projects EVERY image in the cope dir
    
    :projectCopes:
    If True, includes copes and varcopes.  Must be True if you later do a 
    second level analysis, but if you're just looking for stats, zstats and 
    zfstats should suffice
    
    :zstats:
    If True, also projects any z-stats
    
    :zfstats:
    If True, also projects any zf-stats
    
    :preClear:
    If True, deletes the projection dir before projecting
    
    :update:
    Skips any files that already have been projected
    
    :convertOut:
    There is some funkiness with volume-encoded surface files.  NII's can't
    handle dimensions > 2^15 (~32k), so freesurfer reshapes the Nv x 1 files
    (Nv = #vertices) into Nv/rf x rf for an optimal reshaping factor.  HOWEVER,
    there is no guarantee that there is a RF that perfectly shapes the file
    into dimensions < 2^15, so if one does not exist, freesurfer does something 
    funky with the dmensions that isn't supported by other programs.  To fix 
    this, if convertOut is True, the files are loaded into Matlab and Nv is 
    padded with 0's so that the dimensions are ceil(sqrt(Nv)) and other programs
    can read the nii.  Unfortunately, this will have to be undone before loading
    as a surface file in Freesurfer!! Ah, the crazy worlds of incompatible
    standards...
    
    fsaverage and ico surfaces are designed with the appropriate Nv's so that 
    this is not an issue, so the conversion does not run if these are the target
    subjects
    
    requires the freesurfer MRIread and MRIwrite files be on the Matlab path,
    and also my custom function convertVolStructImage, which handles the
    conversion.  You may use convertVolStructImageBack in matlab to undo the
    conversion, and use the file in Freesurfer.  Both functions do nothing if
    the image is already in a compatible format.
    
    :convertAsync:
    if True, calls matlab with acall instead of call, avoiding startup times,
    and license re-checks.  Be sure that await() is called somewhere if
    executing fom a script.
    
    """
    import shutil
    if gfeat and targsubject is None:
        targsubject='fsaverage'
        
    def mkfolder(path, *name):
        fp = p.join(path, *name)
        if preClear and p.exists(fp):
            shutil.rmtree(fp)
        if not p.exists(fp):
            os.makedirs(fp)
        return fp
    
    if reg is None:
        r = p.join(feat, 'reg', 'freesurfer', 'anat2exf.register.dat')
        if p.exists(r):
            reg=r
        elif subject is None:
            raise NotImplementedError()
        
    def project(vol, outfolder, hemi):
        """Simple wrapper function to project a given image"""
        (volpath, volname) = p.split(vol)
        out = fsl.imstrip(p.join(outfolder, volname))+'.nii.gz'
        if update and p.exists(out):
            print 'File %s already exists, skipping'%out
            return
        freesurfer.vol2surf(vol, out, hemi, reg=reg, target=targsubject, 
                            fwhm=fwhm, subject=subject, wait=True)
        if convertOut and not (targsubject=='fsaverage' or targsubject=='ico'):
            import matlab
            try:
                cmd = 'convertVolStructImage %s'%out
                if convertAsync:
                    matlab.acall(cmd)
                else:                                 
                    matlab.call(cmd, wait=False)
            except Exception:
                pass
        
    for hemi in ['lh', 'rh']:
        fname = hemi
        if not targsubject is None:
            fname+='-'+targsubject
        fname += '.surf'
        projfolder = mkfolder(feat, fname)
        
        for design in glob.glob(p.join(feat, 'design.*')):
            (dpath, design) = p.split(design)
            shutil.copyfile(p.join(feat, design), p.join(projfolder, design))
        
        if gfeat:
            # Projects standard images
            for im in ['bg_image', 'mask', 'mean_func']:
                myim = fsl.imglob(os.path.join(feat, im))
                project(myim, projfolder, hemi)
                
            # Projects copes
            copes = glob.glob(p.join(feat, 'cope*.feat'))
            for cope in copes:            
                (cpath, cname) = p.split(cope)
                (cnum, cfeat)=p.splitext(cname)
                
                copedir = p.join(projfolder, cname)
                stats = mkfolder(copedir, 'stats')
                
                # Copy design info
                for design in glob.glob(p.join(cope, 'design.*')):
                    (dpath, design) = p.split(design)
                    shutil.copyfile(p.join(cope, design), p.join(copedir, design))
                
                # Projects basic images
                for im in ['example_func', 'mask', 'mean_func']:
                    myim = fsl.imglob(os.path.join(cope, im))
                    project(myim, copedir, hemi)
                    
                # Projects cope, varcope, degrees of freedom
                project(fsl.imglob(p.join(cope, 'stats', cnum)), stats, hemi)
                project(fsl.imglob(p.join(cope, 'stats', 'var'+cnum)), stats, hemi)
                project(fsl.imglob(p.join(cope, 'stats', 'tdof_t1')), stats, hemi)
        else:
            for im in ['example_func', 'mask', 'mean_func']:
                myim = fsl.imglob(p.join(feat, im))
                (path, myimfile)=p.split(myim)
                shutil.copyfile(myim, p.join(projfolder, myimfile))
            try:
                os.symlink(p.join(feat, 'stats'), p.join(projfolder, 'stats'))
            except:
                pass
            try:
                os.symlink(p.join(feat, 'reg'), p.join(projfolder, 'reg'))
            except:
                pass
            
            # Creates subfolders
            std = mkfolder(projfolder, 'reg_standard')
            stdstats=mkfolder(std, 'stats')
            
            # Projects standard images
            for im in ['example_func', 'mask', 'mean_func']:
                myim = fsl.imglob(p.join(feat, im))
                project(myim, std, hemi)
                
            # Projects stats
            if runAll:
                allroots=['']
            else:
                allroots = ['tdof_t']
                if projectCopes:
                    allroots.extend(['cope', 'varcope'])
                if zstats:
                    allroots.append('zstat')
                if zfstats:
                    allroots.append('zfstat')
                    
            for imroot in allroots:
                for im in glob.glob(p.join(feat, 'stats', imroot+'*')):
                    project(im,stdstats, hemi)
            fsl.junk_reg_standard(projfolder) # avoids need for registration
def parToEV3(par, root, useName=True):
    """Converts a par file to one or more *.ev3 files for use in FSL

    :root:        
    The filenames are {root}_{n}.ev3 for the nth condition, or 
    {root}_{condname}.ev3 if the name is given in the parfile and useName=True

    """
    conds = set(par.cond)

    (head, tail)=os.path.split(root)
    if not os.path.isdir(head):
        os.makedirs(head)
    (root, ext) = os.path.splitext(root)
    
    # Make each ev3 (except ignores rest)
    for c in conds.difference([0]):
        inds = [i for (i, cc) in enumerate(self.cond) if cc==c]
        ev3 = fsl.FslEV3(par.selectSamples(inds))
        evname = root + '_'
        if useName and 'name' in ev3.keys() and not (ev3.name[0]=='' or 
                                                     ev3.name[0] is None):
            evname += ev3.name[0] + '.ev3'
        else:
            evname += '%d.ev3'%c
        ev3['intensities'] = [1]*ev3.nrows
        outorder = ['onsets', 'durations', 'intensities']
        
        # ColumnData can't write a subset of headers, so we must delete them
        for key in ev3.keys():
            if not key in outorder:
                del ev3[key]
                
        ev3.tofile(evname, header=False, header_order=outorder)
def mcDatToFeatExtreg(mcdat, outfile, dof=6):
    """Writes into an fsl FEAT eternal regressors file
    
    If you just want to check 'Add motion parameters to model' in FEAT,
    then outfile should be '{FEATDIR}/mc/prefiltered_func_data_mcf.par'
    and dof should be 6
    
    :dof:
    Number of degrees of freedom to add to model.
    3->translation
    6->+rotation
    9->+scale, but since this is intra-subject, scale is not calculated and 
    can't be used
    """
    assert dof==3 or dof==6
    order = freesurfer.McDat.HEADERS[4:7]
    if dof==6:
        order.extend(freesurfer.McDat.HEADERS[1:4])
    if isinstance(mcdat, str):
        mcdat=freesurfer.McDat(mcdat)
    out = freesurfer.ColumnData(mcdat)
    # ColumnData can't write a subset of headers, so we must delete them
    for key in out.keys():
        if not key in order:
            del out[key]
    (head, tail)=os.path.split(outfile)
    if not os.path.isdir(head):
        os.makedirs(head)
    out.tofile(outfile, header=False, header_order=order)
    
def preRegToFS(featObj, subject, standard='/usr/share/fsl/data/standard/avg152T1_brain.nii.gz', **kwargs):
    """During creation, prepares a Feat object to register to a subject's
    FS anatomy
    
    After the feat is run, you must call postRegToFS otherwise the results will
    not be copied to the anatomical dir! This is handled automatically with 
    regToFS

    If registration has already been run on the anatomical -> std space, this
    doesn't do much other than set the anatomy fields.  If it hasn't been run,
    it runs FLIRT and FNIRT on the anatomy->standard space
    
    :featObj:
    the creation object for a new feat directory
    
    :subject:
    the FS subject
    """
    featObj.setFMRI()
    fslregdir=p.join(freesurfer.SUBJECTS_DIR, subject, 'mri', 'fslreg')
    alreadyRun = p.exists(fslregdir)
    featObj.setFMRI(regstandard=standard, regstandard_yn=1, reghighres_yn=1, reghighres_search=0)
    if alreadyRun:
        featObj.setFMRI(regstandard_search=0,
                        regstandard_nonlinear_yn=0)
    else:
        featObj.setFMRI(regstandard_search=180,
                        regstandard_dof=12, regstandard_nonlinear_yn=1)
    brain = p.join(freesurfer.SUBJECTS_DIR, subject, 'mri', 'brain')
    if not os.path.isfile(brain+'.nii.gz'):
        if os.path.isfile(brain+'.mgz'):
            freesurfer.call('mri_convert %s %s'%(brain+'.mgz', brain+'.nii.gz'))
        else:
            raise RuntimeError('No brain.nii.gz!!')
    featObj.addFiles(brain+'.nii.gz', 4)
    
def regToFS(feat, subject, **kwargs):
    """Sets the FEAT registration to the anatomy of a FS subject,
    and the standard space to avg152
    
    Importantly, it will reuse the anatomical registration to standard space
    if it has already been done.  Also it uses a precomputed FS registration 
    file to register the exf to anatomy, as FLIRT (in my experience) is a 
    terrible coregister, producing files flipped r<->c and cm's off
    
    Note that this must be called *after* Feat has already run
    
    If you are creating a Feat using the Feat object, see preRegToFS and
    postRegToFS.  See them anyway for more details, since this calls them.
    
    :feat:
    path to a feat dir
    
    :subject:
    fs subject
    
    :kwargs:
    :standard: 
    path to standard space.  If none, is not sent (uses default in preReg...)
    
    :reg:
    passed to setReg
    """
    regdir=p.join(feat, 'reg')
    fslregdir=p.join(freesurfer.SUBJECTS_DIR, subject, 'mri', 'fslreg')
    myfeat = fsl.Feat()
    myfeat.setAnalysis(0)
    myfeat.setFMRI(overwrite_yn=1)
    myfeat.addFiles(feat)
    
    preRegToFS(myfeat, subject, **kwargs)
    #myfeat.writeEnding(interactive=True)
    myfeat.execute()
    postRegToFS(feat, subject, **kwargs)
def postRegToFS(feat, subject, reg=None, **kwargs):
    """Updates the registration of a created Feat dir to a FS subject
    
    preRegToFS must have been used in creation of the feat dir, otherwise call
    regToFS
    
    If registration has been done on anatomy->standard space, this copies the
    (computationally expensive) files which are stored in the freesurfer
    subject's dir.  If they were run for the first time in this feat (in
    preRegToFS) then the files are copied from here to the FS subject's dir.
    
    Then, this register's the exf to anatomy using a precomputed registration
    file
    
    :feat:
    path to feat directory
    
    :subject:
    FS subject
    
    :reg:
    See setReg
    """
    regdir=p.join(feat, 'reg')
    fslregdir=p.join(freesurfer.SUBJECTS_DIR, subject, 'mri', 'fslreg')
    alreadyRun = p.isdir(fslregdir)
    if alreadyRun:
        if not p.isdir(regdir):
            os.makedirs(regdir)
        [shutil.copy(f, regdir) for f in glob.glob(p.join(fslregdir, 'highres2standard*'))]
    else:
        os.makedirs(fslregdir)
        [shutil.copy(f, fslregdir) for f in glob.glob(p.join(regdir, 'highres2standard*'))]
    
    setReg(feat, subject, reg=reg)
    
    # Update poststats
    featObj=fsl.Feat()
    featObj.setAnalysis(4)
    featObj.addFiles(feat)
    featObj.updateModel()
    featObj.setFMRI(regstandard_yn=0, reginitial_yn=0, reghighres_yn=0)
    #featObj.writeEnding(interactive=True)
    featObj.execute()
def setReg(feat, subject, reg=None):
    """Sets the registration of a feat directory using a freesurfer register.dat
    
    This will set both exf2anat using the subject's T1 and exf2std
    requires the script reg-setfeat2anat to be on the path
    
    Then, calls updatefeatreg to update all the pretty pics
    :feat:
    the directory
    
    :subject:
    fs subject
    
    :reg:
    path to register.dat.  By default, this is fs.register.dat in the same
    directory as the feat folder
    """
    cmd = 'reg-setfeat2anat --feat %s --s %s'%(feat, subject)
    if not reg is None:
        cmd += ' --reg ' + reg
    freesurfer.call(cmd)
    fsl.call('updatefeatreg %s -pngs'%feat)
    
if __name__ == '__main__':
    #regToFS('/home/scott/data/mri/sessions/mriseComplex3/tc/bold/005/blocks.feat', 'tc')
    #postRegToFS('/home/scott/data/mri/sessions/mriseComplex3/ok/bold/005/blocks.feat', 'ok')
    feat2standard('/home/scott/data/mri/sessions/prakashLocalizers/waseema/vaPre/008/va.feat')