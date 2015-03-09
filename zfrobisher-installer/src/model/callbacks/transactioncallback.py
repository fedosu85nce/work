#
# IMPORTS
#
from yum.callbacks import ProcessTransBaseCallback


#
# CONSTANTS
#
# </empty>


#
# CODE
#
class TransactionCallback(ProcessTransBaseCallback):
    """
    Gets the packages url
    """

    def __init__(self, downloadcallback):
        """
        Constructor

        @type  callback: method
        @param callback: user callback
        """
        # call parent constructor
        ProcessTransBaseCallback.__init__(self)

        # set start lock
        self.__downloadCallback = downloadcallback
    # __init__()

    def event(self, state, data=None):
        """
        Handles the installation process

        @type  state: int
        @param state: Process ID

        @type  data: list
        @param data: list of packages

        @rtype:   None
        @returns: Nothing
        """
        # create empty dict
        packagesUrl = {}

        # data exists: check urls
        if data != None:

            # iterate over packages for packages
            for package in data:

                # get package name and url
                packageUrl = package._remote_url()
                packageSplited = packageUrl.split('/')
                packageName = packageSplited[ (len(packageSplited) - 1) ]

                # fill packages url dict
                packagesUrl[packageName] = packageUrl

            # send packages url to download callback
            self.__downloadCallback.setPackagesUrl(packagesUrl)
    # event()
# TransactionCallback()


