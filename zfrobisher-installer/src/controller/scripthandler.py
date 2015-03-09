#
# IMPORTS
#
from modules.scriptbase import ScriptBase

import logging

#
# CONSTANTS
#
EVT_PRE_INSTALL    = 1
EVT_POST_INSTALL   = 2
EVT_POST_UPGRADE   = 3
EVT_PREPARE_INSTALL = 4


#
# CODE
#
class ScriptHandler(object):
    """
    Manages and executes all scripts of a given event
    """

    def __init__(self):
        """
        Constructor

        @rtype: None
        @returns: Nothing
        """
        # get logger
        self.__logger = logging.getLogger(__name__)

        # list of scripts to be executed
        self.__scripts = []
    # __init__()

    def notify(self, event, arguments):
        """
        Calls all scripts subscribed synchronously by passing the event raised by
        the caller, the scripts are free implement or not the handler for the
        specified event

        @type  event: int 
        @param event: event to be handled

        @type  arguments: dict
        @param arguments: arbitrary arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        # pre install event: handle it
        if event == EVT_PRE_INSTALL:

            self.__logger.debug('Notifying Pre Install Events to:')

            # call onPreInstall for each subscribed script
            for script in self.__scripts:

                try:
                    self.__logger.debug('  * %s' % script.__class__)
                    script.onPreInstall(arguments)

                # script doesn't want to handle it: skip
                except NotImplementedError:
                    continue

        # prepare install event: handle it
        if event == EVT_PREPARE_INSTALL:

            self.__logger.debug('Notifying Prepare Install Events to:')

            # call onPrepareInstall for each subscribed script
            for script in self.__scripts:

                try:
                    self.__logger.debug('  * %s' % script.__class__)
                    script.onPrepareInstall(arguments)

                # script doesn't want to handle it: skip
                except NotImplementedError:
                    continue

        # post install event: handle it
        elif event == EVT_POST_INSTALL:

            self.__logger.debug('Notifying Post Install Events to:')

            # call onPostInstall for each subscribed script
            for script in self.__scripts:

                try:
                    self.__logger.debug('  * %s' % script.__class__)
                    script.onPostInstall(arguments)

                # script doesn't wanto to handle it: skip
                except NotImplementedError:
                    continue

        # post upgrade event: handle it
        elif event == EVT_POST_UPGRADE:

            self.__logger.debug('Notifying Post Upgrade Events to:')

            # call onPostUpgrade for each subscribed script
            for script in self.__scripts:

                try:
                    self.__logger.debug('  * %s' % script.__class__)
                    script.onPostUpgrade(arguments)

                # script doesn't wanto to handle it: skip
                except NotImplementedError:
                    continue
    # notify()

    def subscribe(self, script):
        """
        Adds a script in the list to be able to handle the events triggered here

        @type  script: ScriptBase
        @param script: Script object to handle events

        @rtype: None
        @returns: Nothing
        """
        # script is not a ScriptBase: invalid by contract
        assert isinstance(script, ScriptBase)

        self.__logger.debug('Subscribing %s' % script.__class__)

        # append the script in the list
        self.__scripts.append(script)
    # subscribe()

# ScriptHandler
