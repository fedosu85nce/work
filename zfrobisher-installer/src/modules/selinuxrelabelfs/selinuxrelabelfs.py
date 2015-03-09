#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase

import logging
import os
import subprocess
import traceback


#
# CONSTANTS
#
SELINUX_RELABEL_FILE = '/.autorelabel'


#
# CODE
#
class SelinuxRelabelFS(ScriptBase):
    """
    File system must be relabel on first boot
    """

    def __init__(self):
        """
        Contructor

        @type  name: string
        @param name: network interface name (default = None)
        """
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def onPostUpgrade(self, data):
        """
        Handles the post upgrade event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype:   None
        @returns: Nothing
        """
        try:
            self.onPostInstall(data)

            mountDir = data['model'].get('mountDir')
            if not mountDir:
                return

            # command to restore SELinux configurations
            cmd = "chroot %s chcon -R -t init_exec_t / >> /dev/kop 2>&1" % mountDir

            # SELinux restoration
            subprocess.call(cmd, shell=True)
        except Exception as e:
            self.__logger.critical("Failed SelinuxRelabelFS module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "SELINUXRELABELFS", "POST_MODULES")
    # onPostUpgrade()

# SelinuxRelabelFS
