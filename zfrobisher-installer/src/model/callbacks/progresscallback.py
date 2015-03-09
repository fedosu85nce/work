#
# IMPORTS
#
from urlgrabber.progress import BaseMeter


#
# CONSTANTS
#


#
# CODE
#
class MetadataDownloadCallback(BaseMeter):
    """
    Follow the metadata download progress
    """

    def __init__(self, parseCallback, userCallback):
        """
        Constructor
        
        @type  parseCallback: object
        @param parseCallback: repository parser callback

        @type  userCallback: dict
        @param userCallback: user callback
        """
        # call parent constructor
        BaseMeter.__init__(self)

        # set update frequency as 10 Hz
        self.update_period = 0.1

        # set user callback
        self.__userCallback = userCallback

        # set parser callback
        self.__parseCallback = parseCallback
    # __init__()

    def _do_end(self, amount_read, now=None):
        """
        Download finish callback

        IMPORTANT: the implementation of this method is part of the Yum API for
        callbacks. Do not change the name of this method.

        @type  amount_read: int
        @param amount_read: amount downloaded

        @type  new: float
        @param new: current time

        @rtype: None
        @returns: nothing
        """
        # call user-defined callback
        self.__userCallback({
            'operation': 'download-finish',
            'package': self.filename,
            'url': self.url,
        })

        # set filename in parse callback
        self.__parseCallback.setFileName(self.filename)
    # _do_end()

    def _do_start(self, new):
        """
        Download start callback

        IMPORTANT: the implementation of this method is part of the Yum API for
        callbacks. Do not change the name of this method.

        @type  new: float
        @param new: current time

        @rtype: None
        @returns: nothing
        """
        self.__userCallback({
            'operation': 'download-start',
            'package': self.filename,
            'url': self.url,
        })
    # _do_start()

    def _do_update(self, amount_read, now = None):
        """
        Download progress callback

        IMPORTANT: the implementation of this method is part of the Yum API for
        callbacks. Do not change the name of this method.

        @type  amount_read: int
        @param amount_read: amount downloaded

        @type  new: float
        @param new: current time

        @rtype: None
        @returns: nothing
        """
        # try to calculate download progress percentage
        try:
            percent = 100 * float(amount_read) / self.size

        # division by zero: set percent as zero
        except ZeroDivisionError:
            percent = 0

        # call user-defined callback
        self.__userCallback({
            'operation': 'download',
            'package': self.filename,
            'url': self.url,
            'percent': percent,
        })
    # _do_update()

# MetadataDownloadCallback()


