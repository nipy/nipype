# Contrast & F-tests mode
# real : control real EVs
# orig : control original EVs
set fmri(con_mode_old) real
set fmri(con_mode) real

# Display images for contrast_real 1
set fmri(conpic_real.1) 1

# Title for contrast_real 1
set fmri(conname_real.1) "group mean"

# Real contrast_real vector 1 element 1
set fmri(con_real1.1) 1

# Contrast masking - use >0 instead of thresholding?
set fmri(conmask_zerothresh_yn) 0

# Do contrast masking at all?
set fmri(conmask1_1) 0

##########################################################
# Now options that don't appear in the GUI

# Alternative example_func image (not derived from input 4D dataset)
set fmri(alternative_example_func) ""

# Alternative (to BETting) mask image
set fmri(alternative_mask) ""

# Initial structural space registration initialisation transform
set fmri(init_initial_highres) ""

# Structural space registration initialisation transform
set fmri(init_highres) ""

# Standard space registration initialisation transform
set fmri(init_standard) ""

# For full FEAT analysis: overwrite existing .feat output dir?
set fmri(overwrite_yn) $overwrite
