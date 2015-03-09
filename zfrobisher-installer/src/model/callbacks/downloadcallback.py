#
# IMPORTS
#
from yum.callbacks import DownloadBaseCallback

#
# CONSTANTS
#
FOLLOW_PROGRESS = {
    "operation": "",
    "percent": "",
    "package": "",
    "url": ""
}


#
# CODE
#
class DownloadCallback(DownloadBaseCallback):
    """
    Handles the progress of the download
    """

    def __init__(self, callback, pkgs_num):
        """
        Constructor

        @type  callback: method
        @param callback: user callback
        """
        # call parent constructor
        DownloadBaseCallback.__init__(self)

        # initialize packages URL dictionary
        self.__packagesUrl = {}

        # set user callback
        self.__userCallback = callback

        self.__pkgs_num = pkgs_num
    # __init__()

    def updateProgress(self, name, frac, fread, ftime):
        """
        Updates the progressbar

        @type  name: basestring
        @param name: filename

        @type  frac: float
        @param frac: Progress fraction (0 -> 1)

        @type  fread: basestring
        @param fread: formated string containing BytesRead

        @type  ftime : basestring
        @param ftime : formated string containing remaining or elapsed time
        """
        # space separated name: use only second part
        parts = name.split()

        if len(parts) > 1:
            name = parts[1]

        # name does not have an associated URL: abort
        if name not in self.__packagesUrl:
            return

        # initialize message
        message = {}

        # calculate percentage
        percentage = frac*100

        # create message from template
        message = FOLLOW_PROGRESS.copy()

        # get package URL and name
        message['url'] = self.__packagesUrl[name]
        message['package'] = name

        # percentage is zero: download is starting
        if percentage == 0:
            message['operation'] = 'download-start'

        # percentage is 100: download finish
        elif percentage == 100:
            message['operation'] = 'download-finish'

        # download is in progress
        else:
            message['operation'] = 'download'

        # write percentage
        message['percent'] = percentage

        message['total_pkgs'] = self.__pkgs_num
        # report user callback
        self.__userCallback(message)
    # updateProgress()

    def setPackagesUrl(self, dict):
        """
        Setter for packages url

        @type  dict: dict
        @param dict: dict with packages url

        @rtype:   None
        @returns: Nothing
        """
        self.__packagesUrl = dict.copy()
    # setPackagesUrl()
# DownloadCallback()

