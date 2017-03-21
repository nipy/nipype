# EV title
set fmri(evtitle$ev_num) "$ev_name"

# Basic waveform shape
# 0 : Square
# 1 : Sinusoid
# 2 : Custom (1 entry per volume)
# 3 : Custom (3 column format)
# 4 : Interaction
# 10 : Empty (all zeros)
set fmri(shape$ev_num) 2

# Convolution
# 0 : None
# 1 : Gaussian
# 2 : Gamma
# 3 : Double-Gamma HRF
# 4 : Gamma basis functions
# 5 : Sine basis functions
# 6 : FIR basis functions
# 7 : Optimal/custom basis functions
set fmri(convolve$ev_num) 0

# Apply temporal filtering
set fmri(tempfilt_yn$ev_num) $tempfilt_yn

# Add temporal derivative
set fmri(deriv_yn$ev_num) 0

# Custom EV file
set fmri(custom$ev_num) "$cond_file"
