#
# IMPORTS
#
from modules.partitioner.discinfo import isSAN
from viewer.newt.partitioncfg.partitioner import Partitioner
from viewer.newt.partitioncfg.partition_interface \
    import INDEX_START_PARTITION, INDEX_LIST_ACTIONS, INDEX_BACK
from modules.partitioner.partitioner import VGROOT
from modules.partitioner.partitioner import LVROOT
from modules.partitioner.partitioner import LVBOOT
from modules.partitioner.partitioner import LVSWAP
from model.installfunctions import installSystem
from model.installfunctions import upgradeSystem
from model.licensemodel import getIBMLicense
from model.licensemodel import getNonIBMLicenseNotices
from model.config import *
from subprocess import Popen, PIPE

from confcontroller import ConfController
from scriptfactory import ScriptFactory
from scripthandler import EVT_PRE_INSTALL
from scripthandler import EVT_POST_INSTALL
from scripthandler import EVT_POST_UPGRADE
from zkvmerror import ZKVMError

from __data__ import *

from modules.i18n.i18n import choose_language

import logging
import os
import subprocess
import traceback


#
# CONSTANTS
#
BOOTLOADER_PATH = "/boot/yaboot"
LOG_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
ROOT_DEVICE = "/dev/mapper/%s-%s" % (VGROOT, LVROOT)
GIGABYTES = 1073741824
MIN_DISK_SPACE = 6*1024


#
# CODE
#
class Controller(object):
    """
    Orchestrates the installer
    """

    def __init__(self, model, viewer):
        """
        Constructs the controller

        rtype:   nothing
        returns: nothing
        """
        # create logger
        logging.basicConfig(filename=LIVECD_INSTALLER_LOG,
                            level=logging.DEBUG,
                            format=LOG_FORMATTER)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)

        self.__model = model
        self.__viewer = viewer

        try:
            # fixme:
            # if python-blivet is used later, the udevadm trigger here will be removed
            cmd = "udevadm trigger --action=change --subsystem-match=block"
            subprocess.call(cmd, shell=True)

            # validate log directory
            if not os.path.isdir(ZKVM_LOG_DIR):
                os.makedirs(ZKVM_LOG_DIR)

            self.__scriptController = ScriptFactory()

            # pack event data
            self.__data = {'model': model}

            self.__logger.info("Screen while detecting network")

            firstScreen = viewer.getFirstScreen()
            firstScreen.show()

            # notifies EVT_PRE_INSTALL
            self.__scriptController.notify(EVT_PRE_INSTALL, self.__data)

            # create partitioner instance
            self.__partitioner = Partitioner(self.__logger)
        except ZKVMError as e:
            self.__logger.critical("ZKVMError: %s" % e.getLogCode(e.args))
            self.__createLog()
            self.__viewer.getGeneralTopError().run(e.getCode(e.args))
            self.rebootSystem(True)
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error (INIT).")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            zkvmError = ZKVMError()
            unexpectedCode = zkvmError.getUnexpectedCode("CONTROLLER", "INIT")
            self.__logger.critical("ZKVMError: %s" % zkvmError.getLogCode(unexpectedCode[0]))
            self.__createLog()
            self.__viewer.getGeneralTopError().run(unexpectedCode)
            self.rebootSystem(True)
    # __init__()

    def loop(self):
        """
        Handles the main application loop

        @rtype:   nothing
        @returns: nothing
        """

        try:
            # Check if automated or not
            if self.__data['model'].get('action') in ['install', 'reinstall', 'upgrade']:
                self.automatedInstalls()

            self.__logger.info('Manual mode')
            language = choose_language(self.__viewer)

            # obtain disk information and previous installs
            diskInfoWnd = self.__viewer.getMessageWindow()
            diskInfoWnd.show(GETTING_DISK_INFORMATION.localize())
            #self.__partitioner.getDiskInfo()
            self.__partitioner.detectPreviousInstalls()
            diskInfoWnd.popWindow()

            licenseRet = self.license(language)
            while True:
                if not licenseRet:
                    language = choose_language(self.__viewer)
                    licenseRet = self.license(language)
                    continue

                # start the menu
                rc = self.menu()
                if rc == "back":
                    language = choose_language(self.__viewer)
                    licenseRet = self.license(language)

        except ZKVMError as e:
            self.__logger.critical("ZKVMError: %s" % e.getLogCode(e.args))
            self.__createLog()
            self.__viewer.getGeneralTopError().run(e.getCode(e.args))
            self.rebootSystem(True)
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error (LOOP).")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            zkvmError = ZKVMError()
            unexpectedCode = zkvmError.getUnexpectedCode("CONTROLLER", "LOOP")
            self.__logger.critical("ZKVMError: %s" % zkvmError.getLogCode(unexpectedCode[0]))
            self.__createLog()
            self.__viewer.getGeneralTopError().run(unexpectedCode)
            self.rebootSystem(True)
    # loop()

    def automatedInstalls(self):
        """
        Handles automated installs

        @rtype:   nothing
        @returns: nothing
        """
        try:
            self.__logger.info("Unattended installation (auto mode - kickstart)")

            # Check entitlement
            self.__logger.info("Checking entitlement...")
            if not isEntitled(self.__data):
                self.__logger.critical("Hardware is not entitled, aborting installation!")
                raise ZKVMError("CONTROLLER", "INSTALLPROGRESS", "ENTITLEMENT")

            self.__viewer.getMessageWindow().show(GETTING_DISK_INFORMATION.localize())
            #self.__partitioner.getDiskInfo()
            self.__partitioner.detectPreviousInstalls()

            # automated installation action selected: perform required operations
            if self.__data['model'].get('action') == 'install':

                # get given disk on kickstart
                disk = self.getDiskAutoInstall(self.__data['model'].get('disk'))

                # install system on given disk
                self.__logger.info("Automated install on %s" % disk)
                self.installProgress(disk)

            # automated reinstallation action selected: perform required operations
            elif self.__data['model'].get('action') == 'reinstall':

                self.__logger.info("Automated reinstall")

                # preinstall module can't detect a previous system installed: abort
                if self.__partitioner.detectedPreviousInstall() is False:
                    self.__logger.critical('Automated install failed: no previous system found')
                    self.__viewer.getReinstallError().run()
                    raise ZKVMError("CONTROLLER", "AUTOINSTALL", "NO_PREINSTALL")

                # reinstall process can continue: call correct method
                # important: here the disk is not important, because we already
                # detected it to reinstall the system
                self.installProgress('')

            # automated upgrade action selected: perform required operations
            elif self.__data['model'].get('action') == 'upgrade':
                self.__logger.info("Automated upgrade")
                self.upgradeProgress(False)
            return
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while executing kickstart.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "AUTOINSTALL", "UNEXPECTED_AUTOINSTALL")
    # automatedInstalls()

    def license(self, language):
        """
        Handles the License screen

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger.info('License screen')

        # instantiate the license window for IBM License
        licenseWindow = self.__viewer.getLicenseWindow()

        # display the IBM license in the selected language
        if not licenseWindow.run(getIBMLicense(language, self.__logger), False):
            return False

        # instantiate the license window for Notices
        licenseWindow = self.__viewer.getLicenseWindow()

        # display the Non IBM License and Notices (english only)
        if not licenseWindow.run(getNonIBMLicenseNotices(self.__logger), True):
            self.__logger.info('Non IBM licenses and notices declined, rebooting')
            self.rebootSystem(True)

        self.__data['model'].insert('licenseAccepted', True)

        return True
    # license()

    def menu(self):
        """
        Handles the Menu screen

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger.info('Menu screen')

        # options to be configured on menu screen
        menuOptions = []

        # install option
        menuOptions.append((INSTALL_IBM_ZKVM.localize(), "install"))

        # previous KoP system installed: give more options
        if self.__partitioner.detectedPreviousInstall() is True:
            menuOptions.append((REINSTALL_IBM_ZKVM.localize(), 'reinstall'))
            #menuOptions.append((UPGRADE_INSTALLED_IBM_ZKVM.localize(), 'upgrade'))

        # get menu screen instance
        menuScreen = self.__viewer.getMenu()

        # configure menu options
        menuScreen.setMenuOptions(menuOptions)

        # run menu screen and get the user option
        rc = menuScreen.run()

        if rc[0] == "back":
            return "back"
        else:
            rc = rc[1]

        # user wants to install: call disk screen
        if rc == 'install':
            self.diskSelection()
            return

        # user wants to reinstall system: show a confirmation screen
        elif rc == 'reinstall':
            if self.__partitioner.detectedPreviousInstall():
                installed_disk = self.__partitioner.getPreviousInstalledDisk()
                self.reinstallConfirmation(installed_disk)
                return
            else:
                # no previous installation detected, cannot reinstall
                self.__logger.critical('Reinstall failed: no previous system found')
                self.__viewer.getReinstallError().run()
                raise ZKVMError("CONTROLLER", "REINSTALL", "NO_PREINSTALL")
                return

        # user wants to upgrade: call upgrade process
        elif rc == 'upgrade':
            self.upgradeProgress(True)
            return

        self.__logger.info('Quit to rescue mode')
    # menu()

    def getDiskAutoInstall(self, disk):
        """
        Get and validate the disk device provided by kickstart.

        @type: disk:str
        @params: disk: path disk (can be device, disk-id or disk-label path)

        @rtype: str
        @returns: device disk path to be used by installer
        """
        try:
            self.__logger.info("Getting and validating disk from kickstart.")
            self.__logger.debug("Disk path to be verified: %s" % disk)
            # get disk in case disk-label was provided
            disk = self.getDiskByLabel(disk)

            # get disk in case disk-id was provided
            disk = self.getDiskById(disk)

            # get all available disks
            disks = self.getAvailableDisks()

            # check if provided disk exists in the system.
            if disk.split('/')[-1] not in disks.keys():
                self.__logger.critical("No disk %s found in the system." % disk)
                raise ZKVMError("CONTROLLER", "GETDISKAUTOINSTALL", "NO_DISK")

            # check if the provided disk has the minimun required size.
            if disks[disk.split("/")[-1]][2] < 70:
                self.__viewer.getDiskSelectionError().showErrorDiskSize()
                self.__logger.critical("Invalid disk size (%s) < 70G." % disk)
                raise ZKVMError("CONTROLLER", "GETDISKAUTOINSTALL", "DISK_SIZE")

            self.__logger.debug("Disk path to be used: %s" % disk)
            return disk
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while getting the disk provided by kickstart.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "GETDISKAUTOINSTALL", "UNEXPECTED_AUTOINSTALL")
    # getDiskAutoInstall()

    def getDiskByLabel(self, disk):
        """
        Get the disk path if disk-label was provided.

        @type: disk:str
        @params: disk: path of disk-label

        @rtype: str
        @returns: disk path to be used by installer
        """
        try:
            self.__logger.info("Getting disk by LABEL if applicable...")
            self.__logger.debug("Disk path to be verified (LABEL): %s" % disk)
            diskLabel = None
            # verify if disk provided is disk-label
            if len(disk.split("=")) == 2 and disk.split("=")[0] == 'LABEL':
                diskLabel = "/dev/disk/by-label/%s" % disk.split("=")[1]
            elif disk.startswith("/dev/disk/by-label/"):
                diskLabel = disk

            retDisk = None
            if diskLabel:
                proc = Popen(['readlink', diskLabel], stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                if proc.returncode != 0:
                    self.__logger.critical("Failed to get disk LABEL (%s) (exit code = %s):" % (diskLabel, proc.returncode))
                    self.__logger.critical("%s" % err)
                    raise ZKVMError("CONTROLLER", "GETDISKBYLABEL", "NO_DISK")
                retDisk = out.rstrip()
            else:
                retDisk = disk
            self.__logger.debug("Disk path to be used (LABEL): %s" % retDisk)
            return retDisk
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while disk by label.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "GETDISKBYLABEL", "UNEXPECTED_GETDISKS")
    # getDiskByLabel()

    def getDiskById(self, disk):
        """
        Get the disk path if disk-id was provided

        @type: disk:str
        @params: disk: path of disk-id

        @rtype: str
        @returns: disk path to be used by installer
        """
        try:
            self.__logger.info("Getting disk by ID if applicable...")
            self.__logger.debug("Disk path to be verified (ID): %s" % disk)
            retDisk = None
            # verify if disk provided is disk-id
            if disk.startswith("/dev/disk/by-id/"):
                disks = self.__partitioner.getDisks()
                for d in disks:
                    if d['id'] == disk:
                        # verify if it is multipath
                        if d['mpath_master'] is not None:
                            retDisk = "dev/mapper/%s" % d['mpath_master']
                        else:
                            retDisk = "/dev/%s" % d['name']
                        break
            else:
                retDisk = disk
            if retDisk is None:
                self.__logger.critical("No disk ID found in the system. Exiting...")
                raise ZKVMError("CONTROLLER", "GETDISKBYID",  "NO_DISK")
            else:
                self.__logger.debug("Disk path to be used (ID): %s" % retDisk)
                return retDisk
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while disk by id.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "GETDISKBYID", "UNEXPECTED_GETDISKS")
    # getDiskById()

    def getAvailableDisks(self):
        """
        Get all available disks and return as a list

        @rtype:   list
        @returns: list of disks
        """
        try:
            disks = dict()

            self.__logger.info('DiskSelection screen')

            detdisks = self.__partitioner.getDisks()
            for disk in detdisks:

                # skip if disk is not writable
                if not disk['accessible']:
                    self.__logger.critical('It is not possible to write on %s' % disk['name'])
                    continue

                id = disk['id'].split('/')[4]

                disk_info = [id, int(disk['size']) * int(disk['sectorSize']) / GIGABYTES]

                if disk['mpath_master'] is not None:

                    # filter fibre-channel disks
                    if len(disk['mpath_slaves']) > 0 and isSAN(disk['mpath_slaves'][0]):
                        self.__logger.info('Installation on %s [%s] is not yet supported - FC'
                                           % (disk['mpath_master'], ', '.join(disk['mpath_slaves'])))
                        continue

                    disks[disk['mpath_master']] = [disk['mpath_master']] + disk_info
                    continue

                # filter fibre-channel disks
                if isSAN(disk['name']):
                    self.__logger.info('Installation in %s is not yet supported - FC'
                                       % disk['name'])
                    continue

                disks[disk['name']] = [disk['name']] + disk_info

            return disks
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while verifying disks.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "GETDISKS", "UNEXPECTED_GETDISKS")
    # getAvailableDisks()

    def diskSelection(self):
        """
        Handles the Disk Selection screen

        @rtype:   nothing
        @returns: nothing
        """
        try:
            #Use Blivet to manage all the disks in the system
            #A set used to store all the zfcp LUN that user have specified
            lunset = set()
            # Remove the no disk error check here as user can still add zFCP
            # device later
            self.__logger.info('Disks found: %s' % self.__partitioner.disks)
            while True:
                # run disk selection screen and get the user option
                diskSelected = \
                    self.__viewer.getDiskSelection(self.__partitioner,
                                                   lunset).run()

                # back pressed: go back to main menu
                if diskSelected is None:
                    return
                # No disk selected, continue to show the DiskSelection panel
                if diskSelected == []:
                    continue
                if diskSelected == "addzFCP":
                    while True:
                        addzFCPWindow = self.__viewer.getAddzFCP()
                        rc,devno,wwpn,lun = addzFCPWindow.run()
                        if rc == "back":
                            break
                        # Add 0x prefix if user didn't input it
                        if lun:
                            if lun[:2] != '0x':
                                lun = '0x' + lun
                        res = self.addOneZfcp(devno, wwpn, lun, self.__partitioner.storage, addzFCPWindow)
                        if res == 0:
                            # This SCSI user specified is successfully added,
                            # so add the lun to the LUN set
                            lunset.add(lun)
                            break
                    continue
                # Blivet use MB as unit for size
                totalsize = 0
                for disk in diskSelected:
                    totalsize += disk.size
                # we need at least 6GB for / (5.5G) and /boot (0.5G)
                if totalsize < MIN_DISK_SPACE:
                    self.__viewer.getDiskSelectionError().showErrorDiskSize()
                    # Try disk selection again
                    continue
                self.__logger.info('Disk selected %s' % diskSelected)

                # call next screen
                res = self.installProgress(diskSelected)
                if res == "back":
                    continue
                break
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while selecting disks.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "DISKSEL", "UNEXPECTED_DISKSEL")
    # diskSelection()

    def systemConfigure(self, diskSelected):
        """
        Delegates the configuration phase to config controller
        in order to get user information about root pwd, timezone
        and network.

        @rtype: nothing
        @returns: nothing
        """
        try:
            if self.__data['model'].get('action') not in ('install', 'upgrade', 'reinstall'):
                config = ConfController(self.__model, self.__viewer, self.__data)

                res = config.wizard(diskSelected, self.__partitioner)
                if res == 'back':
                    return res
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while configuring system.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "SYSCONF", "UNEXPECTED_SYSCONF")
    # systemConfigure()

    def installProgress(self, diskSelected):
        """
        Handles the Install screen

        @type  diskSelected: set of DiskDevice
        @param diskSelected: diskname selected by user only used for install

        @rtype:   nothing
        @returns: nothing
        """
        reinstall = False

        # no particular disk select, reinstall
        if not diskSelected:
            reinstall = True
            diskSelected = VGROOT
        index = INDEX_START_PARTITION
        while (True):
            if self.doPartitioning(diskSelected, index) == INDEX_BACK:
                return 'back'
            res = self.systemConfigure(diskSelected)
            # Back to last form of partitioning
            if res == 'back':
                index = INDEX_LIST_ACTIONS
                continue
            else:
                break

        self.__logger.info('InstallProgress screen')

        # get the installer viewer
        install = self.__viewer.getInstallProgress()

        # get problems performing disk operations
        try:

            self.__logger.info('Formatting disks...')
            # reinstall process: reset root device and don't touch on other ones
            if self.__partitioner.detectedPreviousInstall() is True and reinstall:
                install.updateProgress(FORMATTING_ROOT_DEVICE_TO_REINSTALL.localize(), 0)
                self.__partitioner.resetRootDevice()

            # install process: create a default lvm layout on disk
            else:

                # format the disks
                install.updateProgress(FORMATTING_DISKS.localize(), 0)
                #We need to move this function together with other partitioning related functions


        # some error handling disks: abort
        except ZKVMError as e:
            #install.updateProgress(ERROR_WHILE_INSTALLING_IBM_ZKVM.localize() % diskSelected, 30)
            raise
        except Exception as e:
            #install.updateProgress(ERROR_WHILE_INSTALLING_IBM_ZKVM.localize() % diskSelected, 30)
            self.__logger.critical(STR_VERSION + ": Unexpected error while partitioning the disk.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "INSTALLPROGRESSPARTITIONER", "UNEXPECTED_PARTITIONER")

        # get boot, root and swap devices
        boot = self.__partitioner.boot
        root = self.__partitioner.root
        swap = self.__partitioner.swap

        self.__data['model'].insert('bootDevice', boot.path)
        self.__data['model'].insert('rootDevice', root.path)

        diskSelectedStr = ','.join([temp.name for temp in diskSelected])
        try:
            # Copy root file system into the disk
            self.__logger.info("Installing IBM zKVM into disk %s..." % diskSelectedStr)
            install.updateProgress(INSTALLING_IBM_ZKVM_INTO_DISK.localize() % diskSelectedStr, 10)
            # Use only the devices we have now
            installSystem(self.__partitioner, boot, root, swap, install.installInfo, diskSelected,
                          self.__partitioner.getMultipathMode(diskSelected))

        except ZKVMError as e:
            install.updateProgress(ERROR_WHILE_INSTALLING_IBM_ZKVM.localize() % diskSelectedStr, 30)
            raise
        except Exception as e:
            install.updateProgress(ERROR_WHILE_INSTALLING_IBM_ZKVM.localize() % diskSelectedStr, 30)
            self.__logger.critical(STR_VERSION + ": Unexpected error while installing packages.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "INSTALLPROGRESSPACKAGES", "UNEXPECTED_PACKAGES")

        try:
            # notifies EVT_POST_INSTALL
            self.__logger.info('System Installed. Starting post install scripts.')
            install.updateProgress(SYSTEM_INSTALLED_STARTING_POST.localize(), 100)
            self.__scriptController.notify(EVT_POST_INSTALL, self.__data)
        except ZKVMError as e:
            raise
        except Exception as e:
            self.__logger.critical(STR_VERSION + ": Unexpected error while executing post-install modules.")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("CONTROLLER", "INSTALLPROGRESSPOSTINSTALL", "UNEXPECTED_POSTINSTALL")

        self.rebootSystem()
    # installProgress()

    def reinstallConfirmation(self, installed_disk=None):
        """
        Handles the screen to confirm reinstall operation.

        @type  installed_disk: Boolean
        @param installed_disk: The disk where zKVM was installed

        @rtype: None
        @return: Nothing
        """
        self.__logger.info('Confirm reinstall screen')

        # show a message warning about wipe system and get confirmation
        installed_diskId = self.__partitioner.getDiskIdByPath(installed_disk)
        reinstallSystem = self.__viewer.getReinstallConfirmation(installed_diskId).run()

        # user does not desire reinstall system: back to main menu
        if reinstallSystem == 'no':
            return

        # call install screen, and don't care about disk because
        # reinstallation is a controlled process
        self.installProgress('')
    # reinstallConfirmation()

    def upgradeProgress(self, manual):
        """
        Upgrades the hypervisor

        @type  manual: bool
        @param manual: True if manual mode

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger.info('UpgradeProgress screen')

        upgrade = self.__viewer.getUpgradeProgressScreen()

        # manual mode:
        if manual:
            if upgrade.showConfirmationBox(PROCEED_TO_UPGRADE_THE_SYSTEM.localize()) is False:
                # Back to main menu
                return

        # previous KoP system not installed: upgrade is not possible
        if self.__partitioner.detectedPreviousInstall() is False:
            self.__logger.critical("Cannot found installed system, upgrade is not possible!")
            upgrade.showMessageBox(ERROR_CANNOT_DETECT_INSTALLED_SYSTEM.localize())
            # FIXME: Shed some light on what happened, before returning to main menu
            return

        installedVersion = self.__data['model'].get('version')

        # couldn't identify installed version: cannot upgrade
        if installedVersion is None:
            self.__logger.critical("Couldn't identify installed system version, cannot upgrade")
            upgrade.showMessageBox(ERROR_CANNOT_DETECT_INSTALLED_SYSTEM_VERSION.localize())
            # FIXME: Should the upgrade option be removed from main menu, then ?
            return

        # installed version is newer than this current version: cannot upgrade
        elif installedVersion > VERSION:
            self.__logger.critical("Installed system is newer than the system in this package, cannot upgrade")
            upgrade.showMessageBox(ERROR_INSTALLED_SYSTEM_IS_NEWER.localize())
            # FIXME: Should the upgrade option be removed from main menu, then ?
            return

        # installed version is too far behind (2 upgrades difference) the current
        # version: cannot upgrade
        elif installedVersion + 1 < VERSION:
            self.__logger.critical("Cannot fast forward two upgrades at onde")
            upgrade.showMessageBox(ERROR_CANNOT_FAST_FORWARD_UPGRADES.localize())
            # FIXME: Should the upgrade option be removed from main menu, then ?
            return

        self.__logger.info("Starting upgrade...")

        upgrade.showUpgrade()

        # upgrade the system
        if upgradeSystem(ROOT_DEVICE, upgrade.upgradeInfo) is False:
            self.__logger.critical("Upgrade failed!")
            upgrade.showMessageBox(ERROR_UPGRADE_FAILED.localize())
            # Back to main menu
            return

        self.__logger.info('System Upgraded. Starting post upgrade scripts.')

        upgrade.updateProgress(RUNNING_POST_UPGRADE_SCRIPTS.localize(), 90)

        # notifies EVT_POST_UPGRADE
        self.__scriptController.notify(EVT_POST_UPGRADE, self.__data)

        upgrade.updateProgress(UPGRADE_CONCLUDED.localize(), 100)
        self.__logger.info("Upgrade done")

        self.rebootSystem()
    # upgradeProgress()

    def rebootSystem(self, error=False):
        """
        Handles the Reboot system screen

        @type error: boolean
        @param error: reboot due to error

        @rtype:   nothing
        @returns: nothing
        """
        self.__logger.info('RebootSystem screen')

        if error:
            self.__viewer.getRebootSystem().run(error)
        elif not self.__data['model'].get('action'):
        # Only show reboot message is NOT in auto mode
            # message user about rebooting
            self.__viewer.getRebootSystem().run()

        # reboot
        subprocess.call("reboot")
    # RebootSystem()

    def addOneZfcp(self, devno, wwpn, lun, storage, addzFCPWindow):
        '''
        Add the specified SCSI disk to the device tree, all SCSI connected to this zfcp are populated

        @type  devno: String
        @param devno: zFCP device number specified by user

        @type  wwpn: String
        @param wwpn: Worldwild port name specified by user

        @type  lun: String
        @param lun: LUN id specified by user

        @type  storage: Blivet
        @param storage: Blivet instance

        @type  addzFCPWindow: AddzFCP
        @param addzFCPWindow: AddzFCP screen object

        @rtype:   integer
        @returns: addFCP success status
        '''
        zfcp=storage.zfcp
        try:
            zfcp.addFCP(devno,wwpn,lun)
        except Exception as e:
            addzFCPWindow.showError(e.message)
            # Even an error occured, a zFCP device could be set online as well
            # so we need to reset Blivet instance to reflect the lastest state
            storage.devicetree.populate()
            storage.reset()
            return 1
        storage.devicetree.populate()
        storage.reset()
        return 0
    # AddOneZfcp()

    def doPartitioning(self, diskSelected, index):
        partitioning = self.__viewer.getPartitioning(self.__partitioner)
        return partitioning.run(diskSelected, index)

    def __createLog(self):
        """
        Create log after install failure

        @rtype:   nothing
        @returns: nothing
        """
        separator = "===================="
        cmd = []
        # General
        cmd.append("dmesg")
        cmd.append("systemctl status")
        cmd.append("journalctl -xb")
        cmd.append("cat /proc/cmdline")
        cmd.append("cat %s" % KICKSTART_FILE)
        # Network
        cmd.append("ifconfig -a")
        cmd.append("ip address")
        cmd.append("route -n")
        cmd.append("lspci -vv -k")
        cmd.append("ls -la /sys/class/net/")
        cmd.append("ls -la /sys/devices/virtual/net/")
        cmd.append("grep '' /sys/class/net/*/*")
        #cmd.append("cat /sys/class/net/*/carrier")
        #cmd.append("cat /sys/class/net/*/operstate")
        cmd.append("ls -la /etc/sysconfig/network-scripts/")
        cmd.append("cat /etc/sysconfig/network-scripts/ifcfg-*")
        # Disk
        cmd.append("iprconfig -c show-config")
        cmd.append("iprconfig -c show-alt-config")
        cmd.append("iprconfig -c show-ioas")
        cmd.append("multipath -l")
        cmd.append("dmsetup ls")
        cmd.append("pvscan")
        cmd.append("vgscan")
        cmd.append("lvscan")
        cmd.append("ls -la /dev/sd*")
        cmd.append("ls -la /dev/mapper/")
        cmd.append("ls -la /dev/disk/*")
        cmd.append("ls -la /dev/dm-*")
        with open(IBMZKVM_ERROR_LOG, "a") as f:
            for i in cmd:
                proc = Popen(i, shell=True, stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                msg = ">>> COMMAND: %s" % i
                exitCode = ">>> Exit Code: %s" % proc.returncode
                if proc.returncode != 0:
                    exitCode = exitCode + "\n>>> Error messsage: %s" % err
                output = ">>> OUTPUT:\n%s" % out
                f.write("%s\n%s\n%s\n%s\n" % (separator, msg, exitCode, output))
        tarCmd = "tar -zcvf %s %s %s %s" % (IBMZKVM_TARBALL_ERROR_LOG, IBMZKVM_ERROR_LOG, LIVECD_INSTALLER_LOG, LIVECD_PARTITIONER_LOG)
        proc = Popen(tarCmd.split(" "), stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
    # __createLog()
# Controller
