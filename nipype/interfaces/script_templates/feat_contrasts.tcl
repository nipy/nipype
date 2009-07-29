# Contrast & F-tests mode
# real : control real EVs
# orig : control original EVs
set fmri(con_mode_old) orig
set fmri(con_mode) orig

# Display images for contrast_real 1
set fmri(conpic_real.1) 1

# Title for contrast_real 1
set fmri(conname_real.1) "left>right"

# Real contrast_real vector 1 element 1
set fmri(con_real1.1) 1

# Real contrast_real vector 1 element 2
set fmri(con_real1.2) -1.0

# Real contrast_real vector 1 element 3
set fmri(con_real1.3) 1.0

# Real contrast_real vector 1 element 4
set fmri(con_real1.4) -1.0

# Real contrast_real vector 1 element 5
set fmri(con_real1.5) 1.0

# Real contrast_real vector 1 element 6
set fmri(con_real1.6) -1.0

# Real contrast_real vector 1 element 7
set fmri(con_real1.7) 1.0

# Real contrast_real vector 1 element 8
set fmri(con_real1.8) -1.0

# Display images for contrast_orig 1
set fmri(conpic_orig.1) 1

# Title for contrast_orig 1
set fmri(conname_orig.1) "left>right"

# Real contrast_orig vector 1 element 1
set fmri(con_orig1.1) 1

# Real contrast_orig vector 1 element 2
set fmri(con_orig1.2) -1.0

# Real contrast_orig vector 1 element 3
set fmri(con_orig1.3) 1.0

# Real contrast_orig vector 1 element 4
set fmri(con_orig1.4) -1.0

# Real contrast_orig vector 1 element 5
set fmri(con_orig1.5) 1.0

# Real contrast_orig vector 1 element 6
set fmri(con_orig1.6) -1.0

# Real contrast_orig vector 1 element 7
set fmri(con_orig1.7) 1.0

# Real contrast_orig vector 1 element 8
set fmri(con_orig1.8) -1.0

# Contrast masking - use >0 instead of thresholding?
set fmri(conmask_zerothresh_yn) 0

# Do contrast masking at all?
set fmri(conmask1_1) 0

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
set fmri(overwrite_yn) 1
