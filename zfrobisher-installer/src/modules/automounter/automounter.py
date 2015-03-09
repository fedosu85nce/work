#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.partitioner.partitioner import VGROOT
from modules.partitioner.partitioner import LVROOT
from modules.partitioner.partitioner import VGLOG
from modules.partitioner.partitioner import LVLOG
from modules.scriptbase import ScriptBase
from model.disk import isBlockDevice, mount
from model.config import ZKVM_LOG_DIR

import logging
import os
import traceback


#
# CONSTANTS
#
MOUNT_POINT = "/dev/mapper/%s-%s" % (VGROOT, LVROOT)
LOG_PARTITION = "/dev/mapper/%s-%s" % (VGLOG, LVLOG)

#
# CODE
#
class AutoMounter(ScriptBase):
    """
    Auto mount the device block where the root diretory is store
    MUST be the first post install module to be executed
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
        self.onPostInstall(data)
    # onPostUpgrade()

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype:   None
        @returns: Nothing
        """
        try:
            # legacy: handle old vgname for upgrade/reinstall
            mpoint = data['model'].get('rootDevice')
            if not isBlockDevice(mpoint):
                mpoint = '/dev/mapper/vg_root-lv_root'

            if isBlockDevice(mpoint):
                mountDir = mount(mpoint)
                if os.path.isdir(mountDir):
                    data['model'].insert('mountDir', mountDir)
                    self.__logger.debug("Mounted root dir: %s" % mountDir)

                    # create /var/log
                    logDirMountPoint = mountDir + "/var/log"
                    if not os.path.isdir(logDirMountPoint):
                        os.makedirs(logDirMountPoint)
                        self.__logger.debug("%s dir created" % logDirMountPoint)

                    # Get rid of the following lines since we don't have log partition
                else:
                    self.__logger.critical("Failed to mount %s on %s" % (mpoint, mountDir))
            else:
                self.__logger.critical("Invalid mount point (%s)" % mpoint)
        except Exception as e:
            self.__logger.critical("Failed to mount directories on post install")
            self.__logger.critical("Failed AutoMounter module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "AUTOMOUNTER", "POST_MODULES")
    # onPostInstall()

# AutoMounter
