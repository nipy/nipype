# 4mm scale
setscale 4
setoption smoothing 6
clear U
clear UA
clear UB
clear US
clear UP
# try the identity transform as a starting point at this resolution
clear UQ
setrow UQ  1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
optimise 7 UQ  0.0   0.0   0.0   0.0   0.0   0.0   0.0  rel 4
sort U
copy U UA
# select best 4 optimised solutions and try perturbations of these
clear U
copy UA:1-4 U
optimise 7 UA:1-4  1.0   0.0   0.0   0.0   0.0   0.0   0.0  rel 4
optimise 7 UA:1-4 -1.0   0.0   0.0   0.0   0.0   0.0   0.0  abs 4
optimise 7 UA:1-4  0.0   1.0   0.0   0.0   0.0   0.0   0.0  abs 4
optimise 7 UA:1-4  0.0  -1.0   0.0   0.0   0.0   0.0   0.0  abs 4
optimise 7 UA:1-4  0.0   0.0   1.0   0.0   0.0   0.0   0.0  abs 4
optimise 7 UA:1-4  0.0   0.0  -1.0   0.0   0.0   0.0   0.0  abs 4
optimise 7 UA:1-4  0.0   0.0   0.0   0.0   0.0   0.0   0.1  abs 4
optimise 7 UA:1-4  0.0   0.0   0.0   0.0   0.0   0.0  -0.1  abs 4
optimise 7 UA:1-4  0.0   0.0   0.0   0.0   0.0   0.0   0.2  abs 4
optimise 7 UA:1-4  0.0   0.0   0.0   0.0   0.0   0.0  -0.2  abs 4
sort U
copy U UB
# 2mm scale
setscale 2
setoption smoothing 4
clear U
clear UC
clear UD
clear UE
clear UF
# remeasure costs at this scale
measurecost 7 UB 0 0 0 0 0 0 rel
sort U
copy U UC
clear U
optimise 7  UC:1-3  0.0   0.0   0.0   0.0   0.0   0.0   0.0  abs 2
copy U UD
sort U
copy U UF
# also try the identity transform as a starting point at this resolution
sort U
clear U UG
clear U
setrow UG  1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
optimise 7 UG  0.0   0.0   0.0   0.0   0.0   0.0   0.0  abs 2
sort U
copy U UG
# 1mm scale
setscale 1
setoption smoothing 2
setoption boundguess 1
clear U
#also try the identity transform as a starting point at this resolution
setrow UK  1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
optimise 12 UK:1-2  0.0   0.0   0.0   0.0   0.0   0.0   0.0  abs 1
sort U

