__all__ = []

def no_freesurfer():
    from nipype.interfaces.freesurfer import Info
    if Info().version is None:
        return True
    else:
        return False
