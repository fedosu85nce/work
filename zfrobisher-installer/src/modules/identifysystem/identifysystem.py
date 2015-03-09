#!/usr/bin/python


#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from model.disk import mount
from model.disk import umount
from model.config import *
from modules.partitioner.zkvmutils import getstatusoutput
from modules.scriptbase import ScriptBase


import logging
import os
import shutil
import time
import traceback
import urllib

#
# CODE
#
class IdentifySystem(ScriptBase):
    """
    Runs over the system and tries to identify if it was installed using KVM
    on z procedures.
    """

    def __init__(self):
        """
        Contructor

        @rtype: None
        @return: Nothing
        """
        # create logger
        logging.basicConfig(filename=LIVECD_INSTALLER_LOG,
                            level=logging.DEBUG,
                            format=LOG_FORMAT)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)
    # __init__()

    def onPreInstall(self, data):
        """
        Handles the pre install event. Tries to identify if there is some KoP
        installed system.

        Important: actually the default partition scheme for KoP is based on
        LVM entities, used to write system, data, log and swap partitions. Due
        that the following method looks for LVM logical volumns and, according
        a default name for root device, sets a flag to indicate that there
        already is a KoP system installed on machine.
        This partition scheme can change over the time, and if this happens,
        this method must be updated to identify correctly KoP installations.

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype : None
        @return: Nothing
        """
        try:
            self.__logger.debug("onPreInstall() called")

        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Failed IdentifySystem module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "IDSYSTEM", "PRE_MODULES")
    # onPreInstall()

# IdentifySystem
