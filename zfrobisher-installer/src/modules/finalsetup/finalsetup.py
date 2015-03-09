#!/usr/bin/python


#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from modules.grub.grub import Grub
from model.config import ZKVM_LOG_DIR
from model.config import LIVECD_INSTALLER_LOG
from model.config import LIVECD_PARTITIONER_LOG
from model.config import SYSIMG_INSTALLER_LOG
from model.config import SYSIMG_PARTITIONER_LOG
from model.config import STR_VERSION
from subprocess import Popen, PIPE
from modules import product

import logging
import os
import shutil
import subprocess
import traceback


#
# CONSTANTS
#
SYSTEM_DMESG_LOG_FILE = ZKVM_LOG_DIR + "/livecd-dmesg.log"


#
# CODE
#
class FinalSetup(ScriptBase):
    """
    Creates a file that identifies a IBM zKVM installation and execute
    other setups
    """

    def __init__(self):
        """
        Contructor.

        @rtype: None
        @return: Nothing
        """
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def onPostUpgrade(self, data):
        """
        Handles the post upgrade event. Creates a mark file on installed
        system.

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: Nothing
        @return: Nothing
        """
        self.onPostInstall(data)
    # onPostUpgrade()

    def onPostInstall(self, data):
        """
        Handles the post install event. Creates a mark file on installed and
        copy the log file from live image do installed system
        system.

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: Nothing
        @return: Nothing
        """
        try:
            rootMountedDir = None

            # get root directory previously mounted
            rootMountedDir = data['model'].get('mountDir')

            # root directory not mounted: abort
            if rootMountedDir == None:
                return

            # create target log directory
            targetLogDir = rootMountedDir + ZKVM_LOG_DIR
            if not os.path.exists(targetLogDir):
                os.makedirs(targetLogDir)

            # Remove the kop-smt related code and firstlogin.sh
            # add kop-smt service
            #systemdLinkFile = rootMountedDir + '/etc/systemd/system/multi-user.target.wants/kop-smt.service'
            #proc = Popen(['ln', '-sf', '/opt/ibm/zkvm-installer/systemd/kop-smt.service', systemdLinkFile], stdout = PIPE, stderr = PIPE)
            #out, err = proc.communicate()
            #if proc.returncode != 0:
            #    self.__logger.critical("Failed to create synmlink for kop-smt.service (exit code = %s): %s" % (proc.returncode, err))
            #    raise ZKVMError("POSTINSTALL", "FINALSETUP", "NTP_SET")

            # add firstlogin script
            #bashProfile = rootMountedDir + "/root/.bash_profile"
            #with open(bashProfile, "a") as f:
            #    f.write("/opt/ibm/zkvm-installer/scripts/firstlogin.sh\n")

            self.persistentChanges(data)

            # FIXME: need to integrate partitioner log into global log
            # copy log file from live image do installed system
            liveLogFile = LIVECD_INSTALLER_LOG
            systemLogFile = rootMountedDir + SYSIMG_INSTALLER_LOG
            shutil.copy(liveLogFile, systemLogFile)

            partitionerLogFile = LIVECD_PARTITIONER_LOG
            if os.path.isfile(partitionerLogFile):
                with open(partitionerLogFile, "r") as fd:
                    log_content = fd.read()
                if log_content:
                    with open(systemLogFile, "a") as fd:
                        fd.write("\n\n partitioner log: \n\n")
                        fd.write(log_content)

            # copy dmesg output to installed system
            self.__logger.info("Copying LiveCD dmesg output to %s" % SYSTEM_DMESG_LOG_FILE)
            output = subprocess.check_output("dmesg", stderr=subprocess.STDOUT, shell=True)
            outfile = rootMountedDir + SYSTEM_DMESG_LOG_FILE
            with open(outfile, "w") as f:
                f.write(output)

            # copy LiveCD logs (mostly created by kickstart) to the
            # system image
            orig_dir = ZKVM_LOG_DIR
            dest_dir = rootMountedDir + ZKVM_LOG_DIR
            files = os.listdir(orig_dir)
            for f in files:
                orig_file = os.path.join(os.sep, orig_dir, f)
                dest_file = os.path.join(os.sep, dest_dir, f)
                if os.path.isfile(orig_file):
                    shutil.copy(orig_file, dest_file)
                    self.__logger.info("Copied file %s to %s" % (orig_file, dest_file))

            product.refreshProductInfo(rootMountedDir)

        except ZKVMError as e:
            self.__logger.critical("Failed FinalSetup module!")
            raise
        except Exception as e:
            self.__logger.critical("Failed FinalSetup module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "FINALSETUP", "POST_MODULES")
    # onPostInstall()

    def persistentChanges(self, data):
        """
        Persist changes on installed system for both Install and Upgrade.

            @type  data: dict
            @param data: relevant arguments for that given event

            @rtype: Nothing
            @return: Nothing
        """

        # Get mount point for installed system root directory
        rootMountedDir = data['model'].get('mountDir')

            # Override /etc/sysconfig/kernel
        self.__logger.info("Overriding /etc/sysconfig/kernel")
        kernelConf = rootMountedDir + "/etc/sysconfig/kernel"
        kernelConfContent = """UPDATEDEFAULT=yes
DEFAULTKERNEL=kernel
"""
        if os.path.exists(kernelConf):
            os.remove(kernelConf)
        with open(kernelConf, 'w') as fd:
            fd.write(kernelConfContent)

        # Override /etc/selinux/config to enforcing+targeted mode
        self.__logger.info("Overriding /etc/selinux/config")
        selinuxConf = rootMountedDir + "/etc/selinux/config"
        selinuxConfContent = """# This file controls the state of SELinux on the system.
# SELINUX= can take one of these three values:
#     enforcing - SELinux security policy is enforced.
#     permissive - SELinux prints warnings instead of enforcing.
#     disabled - No SELinux policy is loaded.
SELINUX=enforcing
# SELINUXTYPE= can take one of these two values:
#     targeted - Targeted processes are protected,
#     mls - Multi Level Security protection.
SELINUXTYPE=targeted
"""
        if os.path.exists(selinuxConf):
            os.remove(selinuxConf)
        with open(selinuxConf, 'w') as fd:
            fd.write(selinuxConfContent)

        # set /etc/default/grub
        etcDefault = rootMountedDir + "/etc/default"
        etcDefaultGrub = etcDefault + "/grub"
        if not os.path.isdir(etcDefault):
            os.makedirs(etcDefault)
        grub = Grub()
        grub.setDefaultOptions(etcDefaultGrub)

    # persistentChanges()

# FinalSetup
