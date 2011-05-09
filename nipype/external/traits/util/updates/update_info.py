



class UpdateInfo:
    """ Encapsulates the information about the available update or
    updates.  An update can consist of multiple versions, with each
    version containing its own information and download URL.
    """

    # A list of VersionInfo objects
    updates = None

    #========================================================================
    # Constructors
    #========================================================================

    @classmethod
    def from_uri(cls, uri):
        """ Returns a new UpdateInfo, with a populated list of VersionInfo
        objects
        """
        raise NotImplementedError


    def __init__(self, updates=None):
        if updates:
            self.updates = updates
        return

