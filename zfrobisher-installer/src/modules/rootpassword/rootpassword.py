#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase

from subprocess import Popen, PIPE

import fileinput
import logging
import os
import traceback

#
# CONSTANTS
#
SHADOW_FILE = "etc/shadow"


#
# CODE
#
class RootPassword(ScriptBase):
    """
    Set root password.
    """

    def __init__(self):
        """
        Constructor
        """
        self.__logger = logging.getLogger(__name__)
        self.__password = None
        self.__mountDir = None
    # __init__()

    def __autoChangePass(self):
        """
        Set root password (sha512) directly in /etc/shadow (auto mode)

        @rtype   : nothing
        @returns : nothing
        """
        shadowFile = os.path.join(self.__mountDir, SHADOW_FILE)
        os.chmod(shadowFile, 0600)
        searchExp = "root::"
        replaceExp = "root:" + self.__password + ":"
        for line in fileinput.input(shadowFile, inplace=1):
            print line.replace(searchExp, replaceExp),
        os.chmod(shadowFile, 0000)
        self.__logger.debug("%s updated" % shadowFile)
    # __autoChangePass()

    def __manualChangePass(self):
        """
        Set root password (plain text) via passwd command (manual mode)

        @rtype   : nothing
        @returns : nothing
        """
        p1 = Popen(["echo", self.__password], stdout=PIPE)
        p2 = Popen(["passwd", "root", "--stdin"], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        if p2.returncode != 0:
            self.__logger.critical("Failed execute passwd command (exit code = %s): %s" % (p2.returncode, err))
            raise ZKVMError("POSTINSTALL", "ROOTPASSWORD", "ROOT_PWD_MANUAL")
    # __manualChangePass()

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype  : Nothing
        @returns: Nothing
        """
        try:
            self.__logger.info("Executing RootPassword module (EVT_POST_INSTALL).")

            self.__password = data['model'].get('pass')
            self.__mountDir = data['model'].get('mountDir')
            if self.__password:
                self.__autoChangePass()
            else:
                self.__logger.critical("Empty password!")
                raise ZKVMError("POSTINSTALL", "ROOTPASSWORD", "POST_MODULES")
        except ZKVMError as e:
            self.__logger.critical("Failed RootPassword module!")
            raise
        except Exception as e:
            self.__logger.critical("Failed RootPassword module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "ROOTPASSWORD", "POST_MODULES")
    # onPostInstall()

    def run(self, password):
        """
        """
        if password:
            self.__password = password
            self.__manualChangePass()
        else:
            self.__logger.critical("Empty password!")
    # run()
# RootPassword
