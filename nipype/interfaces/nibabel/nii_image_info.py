# Work in Progress
# TO DO- Check if 4D files have any issues, may also want to return other fields

def get_nii_image_info(nifti_input_file):
	"""This module will scan an NII file and return a dictionary with the matrix size as well as the
	x,y and z voxel size in mm"""
	import nibabel as nib
	img = nib.load(nifti_input_file)
	
	img_shape =  img.shape
	img_header = img.get_header().get_zooms()
	dim_x = img_shape[0]
	dim_y = img_shape[1]
	dim_z = img_shape[2]
	vox_size_x = img_header[0]
        vox_size_y = img_header[1]
        vox_size_z = img_header[2]
	""" I also compute the plane with the highest resolution which in theory should represent the image acquisition plane
	but of course you can always resample the image and break these assumptions
	In theory this will fail to yield a value in the event someone cut/resized/did something atypical  to the acquistion window
	Also, there is no absolute requirement that the inplane is a square matrix, so it may be potentially?
	safer to simply determine whch axis is the smallest and assume that is the in plane resolution
	May consider adding an UNKNOWN and/or more checks for this
	image_orientation = 'UNK'
	if(    dim_x  == dim_y ): image_orientation = 'axial'
	elif(  dim_y  == dim_z ): image_orientation = 'sagittal'
	elif(  dim_x  == dim_z ): image_orientation = 'coronal'
	return dim_x, dim_y, dim_z, vox_size_x, vox_size_y, vox_size_z, image_orientation
	REMOVING FROM production version as image_orientation is likely not going to be always correct using this metric
	"""
 	return dim_x, dim_y, dim_z, vox_size_x, vox_size_y, vox_size_z


