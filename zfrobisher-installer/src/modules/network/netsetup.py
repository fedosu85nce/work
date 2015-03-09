#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from modules.network.network import Network

import logging
import traceback

#
# CODE
#
class NetSetup(ScriptBase):
    """
    Represents a network interface
    """

    def __init__(self, name = None):
        """
        Contructor

        @type  name: string
        @param name: network interface name (default = None)
        """
        self.__logger = logging.getLogger(__name__)
        self.__mountDir = None
    # __init__()

    def onPostInstall(self, data):
        """
        Handles the post install event
        @type  data: dict
        @param data: relevant arguments for that given event
        @rtype: None
        @returns: Nothing
        """
        try:
            self.__mountDir = data['model'].get('mountDir')

            self.__logger.debug("Copying network config files from image to installed system...")
            Network.copyConfigFile(self.__mountDir)

            self.__logger.debug("Restarting network services in chrooted installed system...")
            Network.restartNetworkService(self.__mountDir)

            if data['model'].get('ntpservers'):
                Network.setNTP(self.__mountDir)

        except Exception as e:
            self.__logger.critical("Failed NetSetup module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "NETSETUP", "POST_MODULES")
    # onPostInstall()

# NetSetup
