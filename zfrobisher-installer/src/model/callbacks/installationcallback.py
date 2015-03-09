#
# IMPORTS
#
from yum.constants import TS_INSTALL_STATES, TS_ERASE
from yum.rpmtrans import RPMBaseCallback


#
# CONSTANTS AND DEFINITIONS
#
FOLLOW_PROGRESS = { "operation": "",
                    "percent": "",
                    "package": ""
                   }


#
# CODE
#
class InstallationCallback(RPMBaseCallback):
    """
    Handles the progress of the installation
    """

    def __init__(self, callback, num_pkgs):
        """
        Constructor

        @type  callback: method
        @param callback: user callback
        """
        # call parent constructor
        RPMBaseCallback.__init__(self)

        # set user callback
        self.__userCallback = callback
        self.__num_pkgs = num_pkgs

        # create start lock
        self.__startLock = {}
    # __init__()

    def errorlog(self, msg):
        """
        Dummy method. Just ignores any error messages sent from the RPM
        installation process.

        @type  msg: basestring
        @param msg: RPM installation error messages

        @rtype: None
        @returns: nothing
        """
        pass
    # errorlog()

    def event(self, package, action, bytesProcessed, bytesTotal, currentProcess, totalProcess):
        """
        Handles installation progress

        @type  package: basestring
        @param package: A yum package object or simple string of a package name

        @type  action: int
        @param action: A yum.constant transaction set state or in the obscure
                      rpm repackage case it could be the string 'repackaging'

        @type  bytesProcessed: int
        @param bytesProcessed: Current number of bytes processed in the transaction
                           element being processed

        @type  bytesTotal: int
        @param bytesTotal: Total number of bytes in the transaction element being
                         processed

        @type  currentProcess: int
        @param currentProcess: number of processes completed in whole transaction

        @type  totalProcess: int
        @param totalProcess: total number of processes in the transaction.

        @rtype:   None
        @returns: Nothing
        """
        # action is install: get package name and save state
        if action in TS_INSTALL_STATES:
            packageSplited  = package._remote_url().split('/')
            packageName = packageSplited[ len(packageSplited) - 1]
            state = 'install'

        # state is uninstall: get package name and save state
        elif action == TS_ERASE:
            packageName = package
            state = 'uninstall'

        # other action: ignore
        else:
            return

        # calculate percentage
        percentage = (float(bytesProcessed) / float(bytesTotal) ) * 100

        # create message
        message = FOLLOW_PROGRESS

        # lock not exists: operation is starting
        if self.__startLock.get(packageName) == None:
            message['operation'] = '%s-start' % state
            self.__startLock[packageName] = True

        # percentage is 100: operation finish
        elif percentage == 100:
            message['operation'] = '%s-finish' % state

        # operation is running
        else:
            message['operation'] = '%s' % state

        # fill message dict
        message['percent'] = percentage
        message['package'] = packageName
        message['total_pkgs'] = self.__num_pkgs

        # report user callback
        self.__userCallback(message)
    # event()

    def filelog(self, package, action):
        """
        Dummy method. Just ignores any log messages sent from the RPM
        installation process.

        @type  package: basestring
        @param package: package name

        @type  action: basestring
        @param action: RPM installation log message

        @rtype: None
        @returns: nothing
        """
        pass
    # filelog()

    def scriptout(self, package, msgs):
        """
        Dummy method. Just ignores any scriptlet output messages sent from the
        RPM installation process.

        @type  package: basestring
        @param package: package name

        @type  msgs: basestring
        @param msgs: RPM scriptlet output messages

        @rtype: None
        @returns: nothing
        """
        pass
    # scriptout()

# InstallationCallback()
