#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from model.disk import umount, mountEnvironment, umountEnvironment

import logging
import traceback
import subprocess
import os

#
# CODE
#
class AutoUmounter(ScriptBase):
    """
    Auto umount the root diretory is store
    MUST be the last post install module to be executed
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
            mountDir = data['model'].get('mountDir')

            if data['model'].get('licenseAccepted'):
                subprocess.call('touch %s/.zkvm_license_accepted' % mountDir, shell = True)
                self.__logger.info('License accepted')

            self.restoreCon(mountDir, data)

            # umount /
            if not umount(mountDir):
                self.__logger.critical("Failed to umount (%s)" % mountDir)
            else:
                self.__logger.debug("%s umounted successfully" % mountDir)

        except Exception as e:
            self.__logger.critical("Failed AutoUmounter module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "AUTOUMOUNTER", "POST_MODULES")
    # onPostInstall()

    def restoreCon(self, dir, data):
        """
        Does the selinux restorecon

        @type  dir: str
        @param dir: mounted fs

        @type  data: model object
        @param data: model data parameters

        @rtype:   None
        @returns: nothing
        """
        # mount system environment
        self.__logger.debug('restoreCon: mounting environment')
        mountEnvironment(dir)

        # mount zkvm devices
        if not os.path.isdir('%s/var/lib/libvirt/images' % dir):
            os.makedirs('%s/var/lib/libvirt/images' % dir)

        if not os.path.isdir('%s/boot' % dir):
            os.makedirs('%s/boot' % dir)

        # We do not have a lvm for data, so remove these lines
        #self.__logger.debug('restoreCon: mounting data')
        #subprocess.call('mount /dev/mapper/ibmzkvm_vg_data-ibmzkvm_lv_data %s/var/lib/libvirt/images' % dir, shell=True)
        bootDev = data['model'].get('bootDevice')
        if bootDev:
            self.__logger.debug('restoreCon: mounting boot')
            subprocess.call('mount %s %s/boot' % (bootDev, dir), shell=True)
        
        # restorecon to assure all selinux labels are correct
        self.__logger.info('Updating SELinux')
        rc = subprocess.call('chroot %s restorecon -R -F /' % dir, shell=True)

        # force auto relabel if restorecon fails by any reason
        if rc != 0:
            self.__logger.info('SELinux was not restoring successfully, forcing auto-relabel %d' % int(rc))
            subprocess.call('chroot %s touch /.autorelabel' % dir, shell=True)

        else:
            self.__logger.info('SELinux restored')

        self.__logger.debug('restoreCon: umounting devices used for restoreCon')
        # We don't have a lvm for data, so no need to umount
        #subprocess.call('umount %s/var/lib/libvirt/images > /dev/null 2>&1' % dir, shell=True)
        subprocess.call('umount %s/boot > /dev/null 2>&1' % dir, shell=True)
        umountEnvironment(dir)
    # restoreCon()

# AutoUmounter
