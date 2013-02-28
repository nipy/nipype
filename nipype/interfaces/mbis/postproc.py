
def loadParameters( fname ):
    import csv
    import numpy as np

    data = []
    with open( fname ) as csvfile:
        for row in csvfile:
            row = row.replace("[","").replace("]","").replace( " ", "")
            data.append( [ float(val) for val in row.split(',') ] )
    
    nparam = len( data[0] )
    nclasses = int( 0.5 * (nparam*4+1)**0.5 - 0.5 )
    # Load parameters
    mu = []
    sigma = []

    for row in data:
        mu.append( np.matrix( [ float(val) for val in row[0:nclasses] ] ) )
        sigma.append( np.matrix( np.reshape( [ float(val) for val in row[nclasses:] ], (nclasses,nclasses) ) ) )
    
    # Return arrays
    return ( mu, sigma )

def distancePV ( sample, mask, params_tissue1, params_tissue2, distance ):
    from scipy.spatial.distance import mahalanobis,euclidean
    import numpy as np

    # Direction vector between pure tissues
    d_vect = np.ravel(params_tissue2[0] - params_tissue1[0]).T
    mu1 = np.ravel(params_tissue1[0])
    mu2 = np.ravel(params_tissue2[0])
    SI1 = params_tissue1[1].getI()
    SI2 = params_tissue2[1].getI()

    if distance=='mahalanobis':
        norm = np.array( [ 1/(1+ mahalanobis(pix,mu2,SI2)/ mahalanobis(pix,mu1,SI1)) for pix in sample[mask==1] ] )
    elif distance=='dummy':
        norm = mask*0.5
    else:
        norm = np.array( [ 1/(1+ euclidean(pix,mu2)/ euclidean(pix,mu1)) for pix in sample[mask==1] ] )
    result = np.zeros( np.shape( mask ) )
    result[mask==1] = norm
    return result

def computeMAP( tpms, normalize=True ):
    import numpy as np
    normalizer = np.sum( tpms, axis=0 )
    if normalize:
        for tpm in tpms:
            tpm[normalizer>0]/= normalizer[normalizer>0]

    out_seg = np.zeros( shape=tpms[0].shape, dtype=np.uint8 )
    out_seg[normalizer>0] = np.argmax(  tpms, axis=0 )[normalizer>0]
    out_seg[normalizer>0] += 1

    return out_seg, tpms

def fusePV2( in_files, in_maps, parameters, pt_list=( (0,1,2), (2,3), (4,) ), distance='mahalanobis', reorder=True, prefix='./' ):
    import nibabel as nib
    import numpy as np
    import os
    import sys
    import collections
    from scipy.spatial.distance import mahalanobis,euclidean

    nmaps = len( in_maps )
    nclasses = np.shape( parameters )[1]
    assert nmaps == nclasses

    idxs = np.array(range( 0, nclasses ))
    corder = range( 0, nclasses )
    npts = len( pt_list )

    pv_task = np.array([ len(t)>1 for t in pt_list ])  # Check what tissues have pv actions

    if not pv_task.any():
        assert( nmaps == npts )
        return in_maps
    
    # Load probability maps
    initmaps = [ nib.load(f).get_data() for f in in_maps ]

    # If reorder is True, find unordered tissue signatures        
    if reorder:
        means = parameters[0]
        firstmeans = np.array( [ np.ravel(val)[0] for val in means ] )
        idxs = np.argsort(firstmeans)
        corder = np.take(corder, idxs)

    # Load images
    channels = [ nib.load(c) for c in in_files ]

    # Prepare sample
    data_shape = np.shape( channels[0] )
    data_sample = [ channel.get_data().reshape(-1) for channel in channels ]
    data_sample = np.swapaxes( data_sample, 0, 1)

    t_flatten = y=collections.Counter( [element for tupl in pt_list for element in tupl] )
    pt_mapping = [ [ i, [] ] for i in range(0,npts) ] 
    #pv_mapping = [ [ np.where(idxs==i)[0] , [], i ] for i in t_flatten if t_flatten[i]>1 ] 
    pv_mapping = [ [ idxs[i] , [] ] for i in t_flatten if t_flatten[i]>1 ] 
    pt_maps = [ np.zeros( shape=data_shape, dtype=float) for i in range(0,npts)]
    for pt_tuple,out_i in zip( pt_list, range(0,npts) ):
        for t in pt_tuple:
            in_i = idxs[t]
            if t_flatten[t]==1:
                pt_mapping[out_i][1].append( in_i )
                pt_maps[out_i] += initmaps[ in_i ]
            else:
                pvm_id = pv_mapping[:][0].index(in_i)
                pv_mapping[pvm_id][1].append( out_i )

    for m in pv_mapping:
        in_id = m[0]
        neighs = [ pt_mapping[val][1] for val in m[1] ]
        dist = []
        mask = np.zeros(data_shape)
        mask[initmaps[in_id]>0.001] = 1
        mu = []
        SI = []
        out_ids = []
        for n,l in zip(neighs, m[1][:]):
            out_ids.append(l)
            mu.append( parameters[0][n[-1]] )
            SI.append( parameters[1][n[-1]].getI() )
        
        diff = np.zeros( shape=np.shape(mask.reshape(-1)), dtype=float)
        norm = np.array([1/(1+ mahalanobis(pix,mu[1],SI[1])/ mahalanobis(pix,mu[0],SI[0])) for pix in data_sample[mask.reshape(-1)==1]])
        diff[mask.reshape(-1)==1] = norm
        pt_maps[out_ids[0]]+= diff.reshape(data_shape) * initmaps[in_id]
        pt_maps[out_ids[1]]+= (1-diff.reshape(data_shape)) * initmaps[in_id]
        
    # Normalize tpms and compute MAP
    normalizer = np.sum( pt_maps, axis=0 )
    for pt_map in pt_maps:
        pt_map[normalizer>0]/= normalizer[normalizer>0]

    # Generate output names
    ppmnames = [ '%s_pvseg%02d.nii.gz' % ( prefix, i ) for i in range(0,len(pt_maps)) ]

    # Save
    ref = nib.load( in_maps[0] )
    ref = channels[0]
    for i in range(0,len(pt_maps)):
        nii =  nib.Nifti1Image( np.reshape( pt_maps[i], data_shape), ref.get_affine(), ref.get_header() )
        nib.save( nii, ppmnames[i] )

    return ppmnames


def fusePV( in_files, in_maps, parameters, pt_list=[ 0, 2, 4 ], distance='mahalanobis', reorder=True, prefix='./' ):
    import nibabel as nib
    import numpy as np
    import os
    
    nmaps = len( in_maps )
    nclasses = np.shape( parameters )[1]
    assert nmaps == nclasses
    
    corder = range( 0, nclasses )
    npts = len( pt_list )

    if npts == nmaps:
        return in_maps

    pt_list = np.sort( pt_list )

    # Load probability maps
    initmaps = [ nib.load(f) for f in in_maps ]

    # If reorder is True, find unordered tissue signatures        
    if reorder:
        means = parameters[0]
        firstmeans = np.array( [ np.ravel(val)[0] for val in means ] )
        m = np.argsort(firstmeans)
        corder = np.take(corder, m)   
    new_idx = np.take( corder, pt_list )

    # Load images
    channels = [ nib.load(c) for c in in_files ]

    # Prepare sample
    data_shape = np.shape( channels[0] )
    data_sample = [ channel.get_data().reshape(-1) for channel in channels ]
    data_sample = np.swapaxes( data_sample, 0, 1)


    # Split between pv (partial volume) and pt (pure tissue) maps
    pt_niis = []
    pv_niis = []
    pt_param = []

    for tmap,i in zip(initmaps,range(0,nclasses)):
        idx = np.where( new_idx==i )[0]
        if len(idx) == 1:
            pt_niis.append( tmap )
            pt_param.append( [ parameters[0][i], parameters[1][i] ] )
        else:
            pv_niis.append( tmap )

    # Compute the steps required 
    steps = [ val-pt_list[i-1]-1 for val,i in zip( pt_list[1:], range(1,len(pt_list[1:])+1 ) ) ]

    # Extract data and initialize normalizer
    pt_maps = [ m.get_data().reshape(-1) for m in pt_niis ]
    pv_maps = [ m.get_data().reshape(-1) for m in pv_niis ]

    # Process
    for pt_map,i in zip( pt_maps[:-1],range(0,len(pt_maps[:-1])) ):
        curr_steps = steps[i]
        for step in range(1,curr_steps+1):
            pv_idx = (step-1)+i
            pv_map = pv_maps[pv_idx]
            mask = np.zeros( np.shape( pt_map ) )
            mask[pv_map>0.001] = 1

            if not step == curr_steps:  # Direct addition of the pv map to the last pure tissue map
                pt_map+= pv_map
            else:                       # Split pv fraction proportionally to the distance to a contiguous pure tissue
                dist = distancePV( data_sample, mask, pt_param[i], pt_param[i+1], distance )
                pt_map+= dist * pv_map
                pt_maps[i+1]+= (1-dist) * pv_map

    # Normalize tpms and compute MAP
    normalizer = np.sum( pt_maps, axis=0 )
    
    # Generate output names
    ppmnames = [ '%s_pvseg%02d.nii.gz' % ( prefix[:-6], i ) for i in range(0,len(pt_niis)) ]

    # Save
    for i in range(0,len(pt_niis)):
        nii =  nib.Nifti1Image( np.reshape( pt_maps[i], data_shape) , pt_niis[0].get_affine(), pt_niis[0].get_header() )
        nib.save( nii, ppmnames[i] )

    return ppmnames
