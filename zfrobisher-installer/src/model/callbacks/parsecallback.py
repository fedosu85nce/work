#
# SET PATH
#
import sys
sys.path.insert(0, '/usr/share/yum-cli')


#
# IMPORTS
#
from output import CacheProgressCallback


#
# CONSTANTS
#


#
# CODE
#
class MetadataParseCallback(CacheProgressCallback):
    """
    Follow the progress of repository metadata parsing
    """

    def __init__(self, userCallback):
        """
        Constructor

        @type  userCallback: dict
        @param userCallback: usercallback
        """
        # call parent constructor
        CacheProgressCallback.__init__(self)

        # set user callback
        self.__userCallback = userCallback

        # create empty vars
        self.__downloadStarted = []
        self.__filename = ''
    # __init__()

    def progressbar(self, current, total, name=None):
        """
        Show the current progress

        @type  current: int
        @param current: current metadata parsed

        @type  total: int
        @param total: total metadata size

        @type  name: basestring
        @param name: repository name

        @rtype:   None
        @returns: Nothing
        """
        # try to calculate percent
        try:
            percent = (float(current) / float(total)) * 100.0

        # division by zero: set percent as zero
        except ZeroDivisionError:
            percent = 0

        # file download did not start: report and append filename to list
        if not self.__filename in self.__downloadStarted:
            callback = {
                'operation' : 'metadata-parsing-start',
                'task' : self.__filename,
            }
            self.__downloadStarted.append(self.__filename)
        
        # parsing in progress: report
        elif percent < 100.0:
            callback = {
                'operation' : 'metadata-parsing',
                'task' : self.__filename,
                'percent' : percent
            }

        # parse finished: report and remove filename from list
        elif percent == 100.0:
            callback = {
                'operation' : 'metadata-parsing-finish',
                'task': self.__filename
            }
            self.__downloadStarted.remove(self.__filename)
        
        # report progress
        self.__userCallback(callback)
    # progressbar()

    def setFileName(self, filename):
        """
        Sets the file name that being parsed

        @type  filename: basestring
        @param filename: file name

        @rtype: None
        @returns: Nothing
        """
        # set filename
        self.__filename = filename
    # setFileName()

# MetadataParseCallback()
