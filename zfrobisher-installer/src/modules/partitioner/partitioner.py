#!/usr/bin/env python

#
# IMPORTS
#
from discinfo import get_hierarchy_lvm
from discinfo import get_hierarchy_physical
from discinfo import get_hierarchy_raid
from discinfo import get_sector_size
import manage_conventional as conventional
import manage_lvm as lvm
import manage_multipath as multipath
import manage_raid as raid
from model.disk import mount
from model.disk import umount
from model.disk import isBlockDevice
from model.installfunctions import formatPartition
from model.installfunctions import formatSwapPartition
from partitioncommand import PartitionCommand
from zkvmutils import run, getstatusoutput
from controller.zkvmerror import ZKVMError

from controller.zkvmerror import ZKVMError
import traceback

import pprint
import logging
import os
import sys


#
# CONSTANTS AND DEFINITIONS
#
ALL_AVAILABLE = 'all'
CMD_UDEV_SETTLE = 'udevadm settle'
LOG_FILE_NAME = '/var/log/partitioner.log'
LOG_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

VGROOT = 'zkvm'
VGLOG  = 'zkvm_vglog'
VGSWAP = 'zkvm_vgswap'
VGDATA = 'zkvm_vgdata'

LVBOOT = 'boot'
LVROOT = 'root'
LVLOG  = 'log'
LVSWAP = 'swap'
LVDATA = 'data'

NO_PHYSICAL_VOLUMES_FOUND = 'No matching physical volumes found'

CMD_WIPEFS = 'wipefs -a -f %s'

#
# CODE
#
class Partitioner(object):
    """
    Implements all required methods to clean, partition and format disks.
    """

    def __init__(self, logger = None):
        """
        Constructor.

        @type  logger: logging object
        @param logger: reference to logger instance (to log events)

        @rtype: None
        @return: Nothing
        """
        # multipath flag
        self.__hasMultipath = False

        # conventional partition commands
        self.__diskCommands = []

        # lvm partition commands
        self.__lvmCommands = []

        # raid partition commands
        self.__raidCommands = []

        # tolerant mode
        self.__tolerantMode = 0

        # LVM commands
        self.__lvDeleteList = []
        self.__vgDeleteList = []
        self.__pvDeleteList = []
        self.__vgCreateList = []
        self.__pvCreateList = []
        self.__lvCreateList = []
        self.__vgUseList = []
        self.__lvUseList = []

        # store data about disks
        self.__physicalInfo = None
        self.__prevInstalls = None
        self.__lvmInfo = None
        self.__raidInfo = None

        # disk name
        self.__disk = ""

        # disk info
        self.__diskParameters = {}

        # path to prep device
        self.__prepDevice = None

        # path to boot device
        self.__bootDevice = None

        # path to root device
        self.__rootDevice = None

        # path to log device
        self.__logDevice = None

        # path to data device
        self.__dataDevice = None

        # path to swap device
        self.__swapDevice = None

        # configure how to log
        self.__logger = None
        self.__configureLog(logger)
    # __init__()

    def __clearDisks(self, hasMultipath):
        """
        Clears all disks of the system. This cleaning will erase ALL DATA of the
        disks. There is no step back.

        @rtype: None
        @return: Nothing
        """
        try:

            # bug 109358: try to stop all raid partitions. it should be done first
            # in a scenario where there is a LVM on top of a SW RAID. However, in
            # a opposite way (RAID on top of LVM) it will fail. So we just let pass
            # any exception from sw raid.
            try:
                raid.stop()

            except:
                pass

            # delete LVM entities before partitioning
            self.__logger.info('Deleting LVM entities...')
            self.__logger.debug('PV Delete List: %s' % str(self.__pvDeleteList))
            self.__logger.debug('VG Delete List: %s' % str(self.__vgDeleteList))
            self.__logger.debug('LV Delete List: %s' % str(self.__lvDeleteList))

            lvm.delLvmEntities(self.__pvDeleteList,
                               self.__vgDeleteList,
                               self.__lvDeleteList)

            # stop LVM volume groups to avoid problems with disks partitioning
            self.__logger.info('Stopping LVM...')
            lvm.stop()

            # Bug 109358: if SW RAID is on top a LVM we can stop it safetly now
            # because LVM was just stopped above. If any problem happens from now
            # on we need to let the exception raises above.
            raid.stop()

        except ZKVMError as e:
            raise

        except Exception as e:
            self.__logger.critical("Unexpected error")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "ERROR", "ERROR")

        # perform custom setup for multipath devices
        self.__logger.info('Performing custom multipath configuration...')
        self.__logger.debug('Has multipath = %s' % str(hasMultipath))
        tolerantMode = multipath.setup(hasMultipath,
                                       bool(len(self.__lvmCommands)),
                                       bool(len(self.__raidCommands)),
                                       self.__tolerantMode)

        # wait for udev to handle all events
        run(CMD_UDEV_SETTLE)
    # __clearDisks()

    def __configureLog(self, logger = None):
        """
        Configures how to log messages. It's helpful to understand what the
        program does and how to debug it.

        @type  logger: logging object
        @param logger: reference to logger instance (to log events)

        @rtype: None
        @return: Nothing
        """
        # logger instance was given: use it!
        if logger != None and isinstance(logger, logging.Logger):
            self.__logger = logger
            return

        # create logger
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)

        # create file handler and set level to debug
        fileHandler = logging.FileHandler(LOG_FILE_NAME)
        fileHandler.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(LOG_FORMATTER)

        # add formatter to file handler
        fileHandler.setFormatter(formatter)

        # add fileHandler to logger
        self.__logger.addHandler(fileHandler)
    # __configureLog()

    def __createDasdPartitions(self):
        """
        Create single default partition on one dasd disk as specified using fdasd
        @rtype: None
        @return: Nothing
        """
        run('fdasd -a /dev/%s' % self.__disk)
        self.__logger.debug('Fdasd is used to this disk %s' % self.__disk)
    # __createDasdPartitions


    def __createConventionalPartitions(self, hasMultipath, sector_size):
        """
        Calls methods to create conventional partitions on system. Creates LVM
        partitions to allow to expand the system later.

        @rtype: None
        @return: Nothing
        """
        diskpath = ''
        if 'mpath' in self.__disk:
            diskpath = '/dev/mapper/%s' % self.__disk
        else:
            diskpath = '/dev/%s' % self.__disk

        try:
            if sector_size == 512:
                # after deleting all partitions clear the partition table
                self.__logger.debug("Wipefs on %s" % diskpath)
                run('wipefs -f -a %s' % diskpath)

            # wipefs does not consider sector size to remove GPT partition
            # signature. This hack should be here until we have the patch
            # http://www.spinics.net/lists/util-linux-ng/msg09932.html upstream
            else:
                self.__logger.debug("4K disks wipefs issue, using dd")
                run('dd if=/dev/zero of=%s bs=%d count=10000' % (diskpath, sector_size))

            # ensure disks have valid partition tables
            self.__logger.info('Fixing partition tables...')
            conventional.fixPartitionTables(self.__diskCommands)

            # log disks state
            status, output = conventional.logPartitioningScheme()
            self.__logger.debug('Partition scheme:\n\n%s\n\n' % output)

            # delete partitions
            self.__logger.info('Deleting partitions...')
            conventional.deletePartitions(self.__diskCommands, hasMultipath, True)

            # log disks state
            status, output = conventional.logPartitioningScheme()
            self.__logger.debug('Partition scheme:\n\n%s\n\n' % output)

        except Exception as e:
            self.__logger.critical("Unexpected error")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "CONVENTIONAL", "DELETE_PARTITIONS")

        try:
            # create partitions
            self.__logger.info('Creating partitions...')
            conventional.createPartitions(self.__diskCommands, hasMultipath, sector_size)

            # log disks state
            status, output = conventional.logPartitioningScheme()
            self.__logger.debug('Partition scheme:\n\n%s\n\n' % output)

            # wait for udev to handle all events
            run(CMD_UDEV_SETTLE)

        except Exception as e:
            self.__logger.critical("Unexpected error")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "CONVENTIONAL", "CREATE_PARTITIONS")

    # __createConventionalPartitions()

    def __createLVMEntities(self, hasMultipath):
        """
        Calls methods to create LVM entities on system. This method creates all
        required physical volumns, volumn groups and logical volumns to install
        the system.

        @rtype: None
        @return: Nothing
        """
        # can't create PVs: abort
        self.__logger.info('Creating physical volumns...')
        self.__logger.debug('LVM PV Create List:\n%s' % str(self.__pvCreateList))
        if not lvm.createPVs(self.__pvCreateList, hasMultipath):
            raise ZKVMError("PARTITIONER", "LVM", "CREATE_LVM")

        # can't create VGs: abort
        self.__logger.info('Creating volumn groups...')
        self.__logger.debug('LVM VG Create List:\n%s' % str(self.__vgCreateList))
        if not lvm.createVGs(self.__vgCreateList, hasMultipath):
            raise ZKVMError("PARTITIONER", "LVM", "CREATE_LVM")

        # can't create LVs: abort
        self.__logger.info('Creating logical volumns...')
        self.__logger.debug('LVM LV Create List:\n%s' % str(self.__lvCreateList))
        if not lvm.createLVs(self.__lvCreateList):
            raise ZKVMError("PARTITIONER", "LVM", "CREATE_LVM")

        # can't resize LVM entities: abort
        self.__logger.info('Resizing LVMs entities...')
        self.__logger.debug('LVM Reuse List:\n%s' % str(self.__lvUseList))
        if not lvm.resizeLVs(self.__lvUseList):
            raise ZKVMError("PARTITIONER", "LVM", "CREATE_LVM")

        # can't adjust PVs: abort
        self.__logger.info('Adjusting physical volumns...')
        self.__logger.debug('LVM Adjust PVs List:\n%s' % str(self.__vgUseList))
        if not lvm.adjustPVs(self.__vgUseList, hasMultipath):
            raise ZKVMError("PARTITIONER", "LVM", "CREATE_LVM")

        # restart LVM volume groups to avoid any problems later
        self.__logger.info('Restarting LVM...')
        lvm.stop()
        lvm.start(self.__tolerantMode)
    # __createLVMEntities()

    def __createRAIDArrays(self):
        """
        Calls required methods to create RAID arrays on system.

        @rtype: None
        @return: Nothing
        """
        # start RAID arrays to work on them again
        raid.start()

        # create RAID arrays
        raid.createArrays(self.__raidCommands)

        # wait for RAID arrays to become clean
        raid.wait(self.__raidCommands)

        # stop RAID arrays to avoid any problems later
        raid.stop()
    # __createRAIDArrays()

    def getDisksFromType(self, disk_type=None):
        """Get disks from type.

        @rtype: List
        @return: A list containing all disks that match disk type"""

        if self.__physicalInfo == None:
            self.__logger.debug("getDisksFromType(): __physicalInfo == None")
            return

        disks = []
        disks = [disk for disk in self.__physicalInfo if disk['type'] == disk_type]

        return disks
    # getDisksFromType()

    def partitionExists(self, part=None):
        """Return true if part exists on the system.

        @rtype: Boolean
        @return: True if part exists on the system or False if it doesn't"""

        if part == None:
            self.__logger.debug("partitionExists(): part == None")
            return False

        try:
            with open(part, 'r'):
                return True
        except IOError:
            # When /boot partition does not exist, Python throws an
            # IOError exception.  We don't want it to be caught and
            # displayed in UI, so just ignore it.
            self.__logger.debug("partition %s does not exist, ignoring IOError exception")
            pass

        return False
    # partitionExists()

    def getMultipathMaster(self, disk=None):
        """Get multipath master if disk is a slave.

        @rtype: String
        @return: Multipath master device name or None if disk == None"""

        if disk == None:
            self.__logger.debug("getMultipathMaster(): disk == None")
            return None

        if disk['mpath_master'] != None:
            return disk['mpath_master']

        return None
    # getMultipathMaster()

    def sanitizeDiskName(self, disk=None):
        """Append 'mapper/' to disk name.

        @rtype: String
        @return: Disk name sanitized or None if disk is None"""

        if disk == None:
            self.__logger.debug("sanitizeDiskName(): disk == None")
            return

        disk_name = disk['name']
        mpath_master = self.getMultipathMaster(disk)

        if mpath_master != None:
            disk_name = "mapper/{0}".format(mpath_master)

        return disk_name
    # sanitizeDiskName()

    def genBootPartitionName(self, disk_name=None):
        """Generate boot partition name from disk name.

        @rtype: String
        @return: Boot partition name or None if disk name is None"""

        if disk_name == None:
            self.__logger.debug("genBootPartitionName(): disk_name == None")
            return None

        # return disk untouched if already formated
        if disk_name.startswith('/dev'):
            return "{0}2".format(disk_name)

        return "/dev/{0}2".format(disk_name)
    # genBootPartitionName()

    def getBootPartitions(self, disks=None):
        """Get boot partitions from disks.

        @rtype: List
        @return: A list containing all boot partitions, e.g. /dev/sd2,
                 /dev/mapper/mpatha2, from disks"""

        if disks == None:
            self.__logger.debug("getBootPartitions(): disks == None")
            return

        # list of boot partitions
        boot_parts = []

        for disk in disks:
            disk_name = self.sanitizeDiskName(disk)
            boot_part = self.genBootPartitionName(disk_name)

            if self.partitionExists(boot_part):
                boot_parts.append(boot_part)

        return list(set(boot_parts))
    # getBootPartitions()

    def getzKVMBootPartitions(self, boot_parts=None):
        """Get a list of zKVM boot partitions that need to be erased.
        Each boot partition is searched for zKVM strings in grub.cfg.

        @rtype: List
        @return: A list of boot partitions to be erased"""

        if boot_parts == None:
            self.__logger.debug("getzKVMBootPartitions(): boot_parts == None")
            return None

        # mount each partition in boot_parts
        # search for <boot mnt>/grub2/grub.cfg
        # grep 'ibmzkvm_' in grub.cfg
        # add partition to list if above grep is true

        zkvm_boot_parts = []

        for part in boot_parts:
            self.__logger.debug("getzKVMBootPartitions(): part = {0}".format(part))

            mnt = mount(part)
            self.__logger.debug("getzKVMBootPartitions(): mnt = {0}".format(mnt))
            if mnt == None:
                continue

            grubcfg = os.path.join(mnt, "grub2/grub.cfg")
            self.__logger.debug("getzKVMBootPartitions(): grubcfg = {0}".format(grubcfg))

            if os.path.exists(grubcfg):
                self.__logger.debug("getzKVMBootPartitions(): file {0} exists".format(grubcfg))

                with open(grubcfg, 'r') as g:
                    lines = g.readlines()
                    g.close()

                    for line in lines:
                        if VGROOT in line:
                            self.__logger.debug("getzKVMBootPartitions(): {0} found in file {1}, line = {2}".format(VGROOT, grubcfg, line))

                            zkvm_boot_parts.append(part)

                            # found one entry, don't need to continue
                            # reading the lines
                            break

            else:
                self.__logger.debug("getzKVMBootPartitions(): no such file {0}".format(grubcfg))

            if umount(mnt) == False:
                self.__logger.debug("getzKVMBootPartitions(): cannot umount {0} - ignoring".format(mnt))

        return list(set(zkvm_boot_parts))
    # getzKVMBootPartitions()

    def detectzKVMInstalledDisk(self, boot_parts=None):
        """Detect the partition where zKVM is installed.

        @rtype: String
        @return: The disk zKVM is installed or None if none found"""

        if boot_parts == None:
            self.__logger.debug("detectzKVMInstalledDisk(): boot_parts == None")
            return None

        # We need to run pvscan and try to find any of boot_parts in
        # its output.  If matched, it's the disk to be used during
        # reinstall.
        #
        # For example:
        #
        # bash-4.2# pvscan
        #  No matching physical volumes found
        #
        # bash-4.2# pvscan
        #  PV /dev/sda6   VG ibmzkvm_vg_log    lvm2 [10.00 GiB / 0    free]
        #  PV /dev/sda5   VG ibmzkvm_vg_root   lvm2 [20.00 GiB / 0    free]
        #  PV /dev/sda8   VG ibmzkvm_vg_data   lvm2 [41.48 GiB / 0    free]
        #  PV /dev/sda7   VG ibmzkvm_vg_swap   lvm2 [8.00 GiB / 0    free]
        #  Total: 4 [79.47 GiB] / in use: 4 [79.47 GiB] / in no VG: 0 [0   ]

        ret, output = getstatusoutput("pvscan")
        self.__logger.debug("detectzKVMInstalledDisk(): pvscan return: {0}".format(ret))
        self.__logger.debug("detectzKVMInstalledDisk(): pvscan output:\n{0}".format(output))
        if NO_PHYSICAL_VOLUMES_FOUND in output:
            self.__logger.debug("detectzKVMInstalledDisk(): no physical volumes found")
            return None

        # remove numbers from boot_parts, thus we'll have a list of disk names
        disks = [''.join([c for c in part if not c.isdigit()]) for part in boot_parts]

        zkvm_installed_disk = None

        # parse pvscan output
        for line in output.split('\n'):

            if VGROOT in line:
                root_part = line.split()[1]
                pv_name = ''.join([c for c in root_part if not c.isdigit()])

                self.__logger.debug("detectzKVMInstalledDisk(): pv_name = {0}".format(pv_name))

                for disk in disks:
                    self.__logger.debug("detectzKVMInstalledDisk(): disk = {0}".format(disk))

                    if disk == pv_name:
                        self.__logger.debug("detectzKVMInstalledDisk(): disk == pv_name")
                        zkvm_installed_disk = pv_name

        return zkvm_installed_disk
    # detectzKVMInstalledDisk()

    def detectPreviousInstalls(self):
        """Get previous installations of zKVM and populate a dictionary
        with found information.

        @rtype: None
        @return: Nothing"""

        try:
            if self.__physicalInfo == None:
                self.__logger.debug("detectPreviousInstalls(): __physicalInfo == None")
                return

            msdos_disks = self.getDisksFromType('msdos')
            if len(msdos_disks) <= 0:
                self.__logger.debug("detectPreviousInstalls(): msdos_disks = []")
                return

            # all boot partitions available
            boot_parts = self.getBootPartitions(msdos_disks)
            self.__logger.debug("detectPreviousInstalls(): boot_parts = {0}".format(boot_parts))

            # zKVM boot partitions to be erased
            zkvm_boot_parts = self.getzKVMBootPartitions(boot_parts)
            self.__logger.debug("detectPreviousInstalls(): zkvm_boot_parts = {0}".format(zkvm_boot_parts))

            # get the disk zKVM was installed
            zkvm_installed_disk = self.detectzKVMInstalledDisk(boot_parts)
            self.__logger.debug("detectPreviousInstalls(): zkvm_installed_disk = {0}".format(zkvm_installed_disk))

            self._createPreviousInstallsDict(boot_parts, zkvm_boot_parts, zkvm_installed_disk)
            self.__logger.debug("Previous zKVM Installations:")

            for line in pprint.pformat(self.__prevInstalls).split('\n'):
                self.__logger.debug(line)
        except Exception as e:
            self.__logger.critical("Failed NetworkTopology module")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "GET_PREV_INST", "UNEXPECTED")
    # detectPreviousInstalls()

    def getPreviousInstalledDisk(self):
        """Get the disk zKVM was installed.

        @rtype: String
        @return: The disk name zKVM was installed.  None if no
        previous installation is available."""
        return self.__prevInstalls['zkvm_installed_on']
    # getPreviousInstalledDisk()

    def getDiskById(self, disk_name=None):
        """Get the disk by ID from disk name.

        @rtype: String
        @return: Disk by ID or None if disk_name is None"""

        if disk_name == None:
            return None

        # adjust disk name and matching field for comparison
        if 'mpath' in disk_name:
            match_field = 'mpath_master'
            disk = disk_name.replace('/dev/mapper/', '')
        else:
            match_field = 'name'
            disk = disk_name.replace('/dev/', '')

        found_disks = [d for d in self.__physicalInfo if d[match_field] == disk]

        # return first disk id
        for d in found_disks:
            return d['id']

        return "NO DISK-BY-ID FOUND"
    # getDiskById()

    def detectedPreviousInstall(self):
        """Verify if system has any zKVM installation.

        @rtype: Boolean
        @return: True is a zKVM is detected
                 False if no installation was detected"""

        if self.__prevInstalls == None:
            return False

        if self.__prevInstalls['zkvm_installed_on'] != None:
            return True

        return False
    # detectedPreviousInstall()

    def getDiskInfo(self):
        """
        Scans all disks in order to get information about them.

        @rtype: None
        @return: Nothing
        """
        self.__logger.info('Getting current system physical and logical layout')

        # detect disk information
        self.__physicalInfo = get_hierarchy_physical(self.__hasMultipath)
        self.__lvmInfo = get_hierarchy_lvm(self.__physicalInfo)
        self.__raidInfo = get_hierarchy_raid(self.__physicalInfo)

        self.__logger.debug("Physical Info:")
        for line in pprint.pformat(self.__physicalInfo).split('\n'):
            self.__logger.debug(line)

        self.__logger.debug("LVM Info:")
        for line in pprint.pformat(self.__lvmInfo).split('\n'):
            self.__logger.debug(line)

        self.__logger.debug("RAID Info:")
        for line in pprint.pformat(self.__raidInfo).split('\n'):
            self.__logger.debug(line)

        # store disks size
        for disk in self.__physicalInfo:

            diskName = disk['name']
            if disk['mpath_master'] is not None:
                diskName = disk['mpath_master']

            # parameters
            self.__diskParameters[diskName] = {
                'size': disk['size'] * disk['sectorSize'],
                'id'  : disk['id'], 'mpath' : disk['mpath_master'] is not None,
                'slaves' : disk['mpath_slaves'],
            }
    # __getDiskInfo()

    def getDisks(self):
        """
        Get all disks found in the system

        @rtype: dict
        @returns: disks found
        """
        return self.__physicalInfo
    # getDisks()

    def getLVMInfo(self):
        """
        Get LVM data from disks

        @rtype: dict
        @returns: LVM metadata
        """
        return self.__lvmInfo
    # getLVMInfo()

    def getRaidInfo(self):
        """
        Get Raid data from disks

        @rtype: dict
        @returns: Raid metadata
        """
        return self.__raidInfo
    # getRaidInfo()

    def _createPreviousInstallsDict(self, boot_parts=None, zkvm_boot_parts=None, installed_disk=None):
        """Create the dictionary containing the previous installs information.

        @rtype: None
        @return: None if boot_parts is None"""

        if boot_parts == None:
            self.__logger.debug("_createPreviousInstallsDict(): boot_parts == None")
            return None

        # initialize dict
        prev_installs = {}
        prev_installs['boot_parts'] = None
        prev_installs['zkvm_boot_parts'] = None
        prev_installs['zkvm_installed_on'] = None

        # set dict
        prev_installs['boot_parts'] = [part for part in boot_parts]
        if zkvm_boot_parts != None:
            prev_installs['zkvm_boot_parts'] = [part for part in zkvm_boot_parts]
        if installed_disk != None:
            prev_installs['zkvm_installed_on'] = installed_disk

        self.__prevInstalls = prev_installs
    # _createPreviousInstallsDict()

    def __postCleanup(self, selected_disk=None, sector_size=512):
        """
        Remove /boot partitions from previous installations of zKVM.

        @rtype: None
        @return: Nothing
        """
        self.__logger.info("Cleaning previous zKVM /boot partitions...")

        # adjust disk name
        if 'mpath' in selected_disk:
            selected_disk = '/dev/mapper/%s' % selected_disk
        else:
            selected_disk = '/dev/%s' % selected_disk
        self.__logger.debug("selected_disk = %s" % selected_disk)

        if self.detectedPreviousInstall() == True:

            for part in self.__prevInstalls['zkvm_boot_parts']:

                # strip numbers from partition to obtain disk name
                diskname = ''.join([c for c in part if not c.isdigit()])

                self.__logger.debug("part = %s" % part)
                self.__logger.debug("diskname = %s" % diskname)

                if diskname == selected_disk:
                    self.__logger.info("Disk %s was already partitioned, ignoring it" % selected_disk)
                    continue

                if sector_size == 512:
                    # after deleting all partitions clear the partition table
                    cmd = CMD_WIPEFS % part
                    self.__logger.debug("Running %s" % cmd)
                    run(cmd)

                # wipefs does not consider sector size to remove GPT partition
                # signature. This hack should be here until we have the patch
                # http://www.spinics.net/lists/util-linux-ng/msg09932.html upstream
                else:
                    self.__logger.debug("4K disks wipefs issue, using dd")
                    run('dd if=/dev/zero of=%s bs=%d count=1000' % (part, sector_size))

    # __postCleanup()

    def __parseLVMCommands(self):
        """
        Classifies LVM commands.

        @rtype: None
        @return: Nothing
        """
        self.__logger.debug('Parsing LVM commands...')

        # classify lvm commands
        for command in self.__lvmCommands:

            self.__logger.debug('Parsing command = %s' % str(command))

            # delete logical volumn: add it to related list
            if command['command'] == 'delete:logvol':
                cmd = '%s/%s' % (command['vg'], command['name'])
                self.__lvDeleteList.append(cmd)

            # delete volumn group: add it to related list
            elif command['command'] == 'delete:volgroup':
                self.__vgDeleteList.append(command['name'])

            # delete physical volumn: add it to related list
            elif command['command'] == 'delete:phyvol':
                self.__pvDeleteList.append(command['name'])

            # create physical volumn: add it to related list
            elif command['command'] == 'create:pv':
                self.__pvCreateList.append(command)

            # create volumn group: add it to related list
            elif command['command'] == 'create:volgroup':
                self.__vgCreateList.append(command)

            # create logical volumn: add it to related list
            elif command['command'] == 'create:logvol':
                self.__lvCreateList.append(command)

            # use volumn group: add it to related list
            elif command['command'] == 'use:volgroup':
                self.__vgUseList.append(command)

            # use logical volumn: add it to related list
            elif command['command'] == 'use:logvol':
                self.__lvUseList.append(command)
    # __parseLVMCommands()

    def __VGsToRemove(self, disk):
        """
        Returns a list of volume groups that cointais
        the disk passed, it will be used to remove only
        the vgs affected

        @type  disk: str
        @param disk: disk to find LVMs

        @rtype: list
        @returns: list of VGs
        """
        vgsToBeRemoved = []

        self.__logger.debug("disk = %s" % disk)

        # for each volume group found in the system, get the disks used
        # in its physical volume
        for vg, details in self.__lvmInfo['vgs'].iteritems():
            self.__logger.debug("vg = %s" % vg)
            self.__logger.debug("details = %s" % details)

            # we certainly need to remove any other vg created
            # by us or the installation will fail
            if 'ibmzkvm_vg_' in vg:
                self.__logger.debug("Found a previous zKVM vg: %s" % vg)
                vgsToBeRemoved.append(vg)
                continue

            # for any other VG, check if the disks used are going to
            # be used now

            # details['pvsToLvs'] can be disks (sdb, mapper/mpathb) or
            # partitions (sdb3, mapper/mpathb8).
            for element in details['pvsToLvs']:
                self.__logger.debug("element = %s" % element)

                # strip any number from element
                element = ''.join([c for c in element if not c.isdigit()])

                # strip "mapper/" from element
                if 'mapper/' in element:
                    element = element.replace("mapper/", "")

                self.__logger.debug("stripped element = %s" % element)

                if disk == element:
                    self.__logger.debug("disk == element")

                    # FIXME: the correct way would be reducing the vg,
                    # not removing it.
                    vgsToBeRemoved.append(vg)

        return vgsToBeRemoved
    # __VGsToRemove()

    # TODO: specify vgs to be removed as well
    def __PVsToRemove(self, disk):
        pvsToBeRemoved = []

        # add physical volumns to be removed
        for pv in list(self.__lvmInfo['pvs']):
            self.__logger.debug("pv = %s" % pv)

            # skip pvs that does not belong to the LVM to be
            # destroyed

            # Here, the physical volume (pv) can be, for
            # example, "sdcn8" or "sdcn20" or whatever pv is
            # in the array list.  We need to obtain the real
            # disk name from this pv, i.e. if we strip numbers
            # from "sdcn8" or "sdcn20" we get "sdcn" which
            # might be the disk user selected during
            # installation.
            pv_no_digits = ''.join([c for c in pv if not c.isdigit()])

            # pv can be "mapper/mpathb8", strip "mapper/" from it
            if 'mapper/' in pv_no_digits:
                pv_no_digits = pv_no_digits.replace("mapper/", "")

            self.__logger.debug("disk = %s" % disk)
            self.__logger.debug("pv_no_digits = %s" % pv_no_digits)

            if disk == pv_no_digits:
                pvsToBeRemoved.append(pv)

        return pvsToBeRemoved
    # __PVsToRemove()

    def __prepareToClean(self, disk):
        """
        Gets all data gathered from disks and prepares the commands to clean
        them completely.

        #FIXME: create policies to create commands to clean only the disk which
        the system is installed. At this moment the given disk is completely
        erased, but all LVM entities are also cleaned up.

        @type  disk: str
        @param disk: disk to be partitioned

        @rtype: None
        @return: Nothing
        """
        # no disk information: abort
        if ((self.__physicalInfo == None) or
            (self.__lvmInfo == None) or
            (self.__raidInfo == None)):
            raise ZKVMError('PARTITIONER', 'DISK', 'INFORMATION')

        # disk has RAID: append commands to remove it correctly
        if len(self.__raidInfo.keys()) > 0:

            # to be implemented
            self.__logger.info('RAID elements not supported')

        # disk has LVM: append commands to remove it correctly
        # FIXME: implement policies to allow to clean only LVM entities that
        # have the given disk that will be erased
        if len(self.__lvmInfo.keys()) > 0:
            self.__logger.info('Preparing to clean LVM elements on system...')

            # get only LVMs affected
            vgsToRemove = self.__VGsToRemove(disk)

            # add volumn groups to be removed
            for vg in vgsToRemove:
                cmd = {'command': 'delete:volgroup', 'name': vg}
                self.__lvmCommands.append(cmd)
                for line in pprint.pformat(cmd).split('\n'):
                    self.__logger.debug(line)

            # get physical volumes to be removed
            pvsToRemove = self.__PVsToRemove(disk)

            # add physical volumes to be removed
            for pv in pvsToRemove:
                cmd = {'command': 'delete:phyvol', 'name': pv}
                self.__lvmCommands.append(cmd)
                for line in pprint.pformat(cmd).split('\n'):
                    self.__logger.debug(line)

        # get current partition scheme on disk and create commands to remove it
        for d in self.__physicalInfo:
            self.__logger.info('Preparing to clean previous partitions...')

            # disk not selected: skip it
            if d['name'] != disk:
                continue

            # run over partitions
            for partition in d['parts']:

                # partition is empty: get next one
                if partition['name'] == 'empty':
                    continue

                diskName = '/dev/' + d['name']
                if d['mpath_master'] is not None:
                    diskName = '/dev/mapper/' + d['name']

                # create command
                cmd = {'nr': partition['nr'],
                       'command': 'delete:partition',
                       'name': partition['name'],
                       'disk_name': diskName}

                # add to commands list
                self.__diskCommands.append(cmd)

                # debug-log cmd
                for line in pprint.pformat(cmd).split('\n'):
                    self.__logger.debug(line)
    # __prepareToClean()

    def __run(self, hasMultipath, sector_size):
        """
        Executes all steps to clean, partition and format the disks.

        @rtype: None
        @return: Nothing
        """
        self.__logger.info('Starting partitioner module')

        self.__logger.debug("Disk Commands:")
        for line in pprint.pformat(self.__diskCommands).split('\n'):
            self.__logger.debug(line)

        self.__logger.debug("LVM Commands:")
        for line in pprint.pformat(self.__lvmCommands).split('\n'):
            self.__logger.debug(line)

        self.__logger.debug("RAID Commands:")
        for line in pprint.pformat(self.__raidCommands).split('\n'):
            self.__logger.debug(line)

        try:
            # prepare info to clean the disks
            self.__prepareToClean(self.__disk)

            # parse lvm commands
            self.__parseLVMCommands()

            # clear all disks
            self.__clearDisks(hasMultipath)

            # create conventional partitions
            #fixme:
            #This is only a quick work around for DASD partitioning.
            #We will switch to blivet or switch to another more
            #general function to cover both DASD and zFCP.
            self.__createDasdPartitions()

            # create lvm entities to allow to expand the system later
            self.__createLVMEntities(hasMultipath)

            # remove previous zKVM /boot partitions
            self.__postCleanup(self.__disk, sector_size)

        except ZKVMError as e:
            raise

        except Exception as e:
            self.__logger.critical("Unexpected error")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "ERROR", "ERROR")

        self.__logger.info('Process done')
    # __run()

    def createDefaultLVMLayout(self, diskName, mpath=False):
        """
        Receives all required parameters to create a default LVM layout on
        selected disk.

        @type  diskName: str
        @param diskName: disk to be formatted

        @type  mpath: bool
        @param mpath: multipath flag

        @rtype: bool
        @return: True if everything is ok, False otherwise
        """
        self.__disk = diskName

        # given disk is not valid: abort
        if diskName not in self.__diskParameters.keys():
            raise ZKVMError("PARTITIONER", "DISK", "NO_DISK")

        try:
            # partitioning dictionary creator
            sectors = 512
            if self.__diskParameters[diskName]['mpath']:
                slave = self.__diskParameters[diskName]['slaves'][0]
                sectors = get_sector_size(slave)

            else:
                sectors = get_sector_size(diskName)

            scheme = PartitionCommand(sectors)

            # configure parameters to create the commands
            scheme.setDisk(diskName)
            scheme.setDiskId(self.__diskParameters[diskName]['id'])
            scheme.setDiskSize(self.__diskParameters[diskName]['size'])
            scheme.setMultipathMode(self.__diskParameters[diskName]['mpath'])
            self.__hasMultipath = self.__diskParameters[diskName]['mpath']

            # partition sizes
            # 'prep': 8Mb
            # 'boot': 512Mb
            #    'swap': 4Gb
            #    'root': all
            partitionSizes = {
                'boot': 512 * 1024
            }

            # table of logical partition, containing root and swap
            logicalVolumeTable = {
                'boot': 512 * 1024,
                'swap': (8 * 1024 * 1024),
                'root': (12 * 1024 * 1024)
            }

            # create partition boot and root
            self.__logger.info("Creating partition...")
            root = scheme.createPartition(None, 'Log', 'lvm', ALL_AVAILABLE, VGROOT, 1)
            self.__logger.debug("partition root: root = %s" % root)
            self.__diskCommands += [root]
            self.__logger.debug("disk commands: %s" % self.__diskCommands)

            # lvm commands
            self.__logger.info("Creating physical volume...")
            pv_root = scheme.createPhysicalVolume(root['disk_name'], root['size'], root['name'])
            self.__logger.debug("physical volume: %s" % pv_root)
            self.__lvmCommands += [pv_root]
            self.__logger.debug("lvm commands: %s" % self.__lvmCommands)

            # create volume group
            vg_root = scheme.createVolumeGroup([root['name']], VGROOT)
            self.__lvmCommands += [vg_root]

            # create logical volume
            self.__logger.info("Creating logical volume...")
            lv_boot = scheme.createLogicalVolume(root['vg'], 'ext3', LVBOOT, '/boot', logicalVolumeTable['boot'])
            self.__logger.debug("configing boot vloume: %s" % lv_boot)
            lv_root = scheme.createLogicalVolume(root['vg'], 'ext3', LVROOT, '/', logicalVolumeTable['root'])
            self.__logger.debug("configing root vloume: %s" % lv_root)
            lv_swap = scheme.createLogicalVolume(root['vg'], 'swap', LVSWAP, '', logicalVolumeTable['swap'])
            self.__logger.debug("configing swap vloume: %s" % lv_swap)
            self.__lvmCommands += [lv_root, lv_boot, lv_swap]

            # run partitioner instructions to clean and partition the disk
            self.__run(self.__diskParameters[diskName]['mpath'], sectors)
            # update prep, boot, root, log, data and swap paths
            path = '/dev/%s'
            if self.__diskParameters[diskName]['mpath']:
                path = '/dev/mapper/%s'
            #self.__prepDevice = path % prep['name']
            self.__bootDevice = '/dev/mapper/%s-%s' % (vg_root['name'], lv_boot['name'])
            self.__rootDevice = '/dev/mapper/%s-%s' % (vg_root['name'], lv_root['name'])
            self.__swapDevice = '/dev/mapper/%s-%s' % (vg_root['name'], lv_swap['name'])
            #self.__logDevice  = '/dev/mapper/%s-%s' % (vg_log['name'], lv_log['name'])
            #self.__dataDevice = '/dev/mapper/%s-%s' % (vg_data['name'], lv_data['name'])
            #self.__swapDevice = '/dev/mapper/%s-%s' % (vg_swap['name'], lv_swap['name'])

            # devices to be formatted as ext4
            devices = [
                self.__bootDevice,
                self.__rootDevice
                #self.__logDevice,
                #self.__dataDevice
            ]

            # format devices
            for dev in devices:
                if formatPartition(dev) == False:
                    raise ZKVMError("PARTITIONER", "FORMAT", "ERROR")

            # devices to be formatted as swap
            swapDevices = [self.__swapDevice]

            # format swap devices
            for dev in swapDevices:
                if formatSwapPartition(dev) == False:
                    raise ZKVMError("PARTITIONER", "FORMAT", "ERROR")

        except ZKVMError as e:
            raise

        except Exception as e:
            self.__logger.critical("Unexpected error")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PARTITIONER", "ERROR", "ERROR")

        return True
    # createDefaultLVMLayout()

    def getBootDevice(self):
        """
        Returns complete path to boot device.

        @rtype: str
        @return: path to prep device
        """
        return self.__bootDevice
    # getBootDevice()

    def getDataDevice(self):
        """
        Returns complete path to data device.

        @rtype: str
        @return: path to data device
        """
        return self.__dataDevice
    # getDataDevice()

    def getLogDevice(self):
        """
        Returns complete path to log device.

        @rtype: str
        @return: path to log device
        """
        return self.__logDevice
    # getLogDevice()

    def getMultipathMode(self):
        """
        Returns multipath mode.

        @rtype: bool
        @return: multipath mode
        """
        return self.__hasMultipath
    # getMultipathMode()

    def getPrepDevice(self):
        """
        Returns complete path to prep device.

        @rtype: str
        @return: path to prep device
        """
        return self.__prepDevice
    # getPrepDevice()

    def getSwapDevice(self):
        """
        Returns complete path to swap device.

        @rtype: str
        @return: path to swap device
        """
        return self.__swapDevice
    # getSwapDevice()

    def getRootDevice(self):
        """
        Returns complete path to root device.

        @rtype: str
        @return: path to root device
        """
        return self.__rootDevice
    # getRootDevice()

    def getTolerantMode(self):
        """
        Returns tolerant mode.

        @rtype: int
        @return: tolerant mode
        """
        return self.__tolerantMode
    # getTolerantMode()

    def resetRootDevice(self):
        """
        Formats root device (according LVM default scheme) and adjusts all
        pointers to allow reinstall the system correctly.

        Important: this method is directly related to LVM default partitioning
        scheme. It assumes that root device is under /dev/mapper/vg_root-lv_root
        path. If this default scheme changes on future, this method must be
        revisited to assure its functionality.

        @rtype: bool
        @return: True if everything is ok, False otherwise
        """
        # restart LVM volume groups to assure its functionality
        self.__logger.info('Restarting LVM...')
        lvm.stop()
        lvm.start(self.__tolerantMode)
        
        # wait for udev to handle all events
        if run(CMD_UDEV_SETTLE) != 0:
            raise RuntimeError('Error: udevadm settle failure')

        # Do not trust content from / partition.  User can screw up
        # with its / partition and try a reinstall to fix it.  Thus
        # our code cannot trust on reading content from old and dirty
        # / partition.  We can just infere /boot partition by
        # appending 2 to the detected disk.
        installed_disk = self.getPreviousInstalledDisk()
        boot_partition = self.genBootPartitionName(installed_disk)
        self.__bootDevice = boot_partition

        # check multipath
        self.__hasMultipath = self.__diskParameters[installed_disk.split('/')[-1]]['mpath']

        # as consequence, configure prep device path
        self.__prepDevice = self.__bootDevice[:-1] + "1"

        # update root, log, data and swap paths
        self.__rootDevice = '/dev/mapper/%s-%s' % (VGROOT, LVROOT)
        self.__logDevice  = '/dev/mapper/%s-%s' % (VGLOG, LVLOG)
        self.__dataDevice = '/dev/mapper/%s-%s' % (VGDATA, LVDATA)
        self.__swapDevice = '/dev/mapper/%s-%s' % (VGSWAP, LVSWAP)

        self.__logger.debug("resetRootDevice(): __prepDevice = %s" % self.__prepDevice)
        self.__logger.debug("resetRootDevice(): __bootDevice = %s" % self.__bootDevice)
        self.__logger.debug("resetRootDevice(): __rootDevice = %s" % self.__rootDevice)
        self.__logger.debug("resetRootDevice(): __logDevice = %s" % self.__logDevice)
        self.__logger.debug("resetRootDevice(): __dataDevice = %s" % self.__dataDevice)
        self.__logger.debug("resetRootDevice(): __swapDevice = %s" % self.__swapDevice)

        # format boot, root and swap devices
        formatPartition(self.__bootDevice)
        formatPartition(self.__rootDevice)
        formatSwapPartition(self.__swapDevice)

        return True
    # resetRootDevice()

    def setMultipathMode(self, mode=False):
        """
        Configures multipath mode.

        @type  mode: bool
        @param mode: multipath mode (default = False)

        @rtype: None
        @return: Nothing
        """
        self.__hasMultipath = mode
    # setMultipathMode()

    def setTolerantMode(self, mode):
        """
        Sets tolerant mode.

        @type  mode: int
        @param mode: tolerant mode
        """
        self.__tolerantMode = mode
    # setTolerantMode()

# Partitioner
