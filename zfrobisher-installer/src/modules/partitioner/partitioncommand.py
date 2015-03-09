#!/usr/bin/env python

#
# IMPORTS
#


#
# CONSTANTS AND DEFINITIONS
#
ALL_AVAILABLE = 'all'
EXTENT_SIZE = 4096
MEGABYTE = 1024
MAX_SECTOR_POSSIBLE = 4294967295


#
# CODE
#
class PartitionCommand(object):

    def __init__(self, sectorSize):
        """
        Constructor

        @rtype:   nothing
        @returns: nothing
        """
        # disk parameters
        self.__disk = ""
        self.__diskSize = 0
        self.__diskId = ""
        self.__sectorSize = sectorSize
        self.__sectorOffset = int(1024 / (self.__sectorSize / float(MEGABYTE)))
        self.__extEndSector = 0

        # flag to indicate multipath
        self.__hasMultipath = False

        # start sector pointer (primary partitions)
        self.__primaryStartPoint = self.__sectorOffset
    # __init__()

    def createLogicalVolume(self, vg, filesystem, name, mountpoint, size):
        """
        Creates a logical volume partition

        @type  vg: str
        @param vg: volume group name

        @type  filesystem: str
        @param filesystem: filesystem to format this partition

        @type  name: str
        @param name: lv name

        @type  mountpoint: str
        @param mountpoint: mount point of this partition

        @type  size: int
        @param size: partition size

        @rtype:   dict
        @returns: logical volume commands
        """
        lv = {}
        lv['command'] = 'create:logvol'
        lv['vg'] = vg
        lv['fs'] = filesystem
        lv['size'] = size - EXTENT_SIZE + 1
        lv['name'] = name
        lv['mountPoint'] = mountpoint
        lv['format'] = 'yes'

        return lv
    # createLogicalVolume()

    def createPartition(self, mp, mtype, fs, size, vg, nr):
        """
        Creates a conventional partition

        @type  mp: str
        @param mp: mount point of this partition

        @type  mtype: str
        @param mtype: partition type (Pri, Ext, Log)

        @type  fs: str
        @param fs: filesystem to format this partition

        @type  size: int
        @param size: partition size

        @type  vg: str
        @param vg: volume group name

        @type  nr: int
        @param nr: partition number

        @rtype:   dict
        @returns: partition commands
        """
        startSector = 0
        endSector = 0

        # primary partition: calculate the space according instructions below
        if mtype == 'Pri':

            # calculate the start sector
            startSector = self.__primaryStartPoint

            # calculate the end sector
            sectorLen = startSector + int(size * MEGABYTE / float(self.__sectorSize))
            endSector = sectorLen - 1
            self.__primaryStartPoint = sectorLen

            # decrease disk size
            self.__diskSize -= size

        # extended partition: update primary and logical pointers
        # when a extended partition is given, its size is not taken into account
        elif mtype == 'Ext':

            # calculate the start sector
            startSector = self.__primaryStartPoint

            # calculate end sector pointer
            endSector = int(self.__diskSize * MEGABYTE / float(self.__sectorSize)) + startSector - 1
            if endSector > MAX_SECTOR_POSSIBLE:
                endSector = MAX_SECTOR_POSSIBLE

            self.__extEndSector = endSector

            # decrease disk size
            self.__diskSize -= EXTENT_SIZE - 1

        # logical partition: calculate the space according instructions below
        elif mtype == 'Log':

            # FIXME, need to improve
            # just for zkvm without extended partition
            self.__extEndSector = endSector
            # refresh start sector pointer
            startSector = self.__primaryStartPoint + self.__sectorOffset

            if size == ALL_AVAILABLE:
                endSector = self.__extEndSector
                size = self.__diskSize - 1
                self.__diskSize = 0

            else: 
                # calculate end sector pointer
                sectorLen = startSector + int(size * MEGABYTE / float(self.__sectorSize))
                endSector = sectorLen - 1
                self.__primaryStartPoint = sectorLen

                # decrease disk size
                self.__diskSize -= size


        part = {}
        part['command'] = 'create:partition'
        part['id'] = "%s-part%s" % (self.__diskId, str(nr))
        part['name'] = self.__disk + str(nr)
        part['mount_point'] = mp
        part['type'] = mtype
        part['fs'] = fs
        part['multipath'] = self.__hasMultipath
        part['raid_name'] = None
        part['disk_name'] = '/dev/%s' % self.__disk
        part['size'] = size
        part['vg'] = vg
        part['nr'] = nr
        part['format'] = True
        part['start'] = startSector
        part['end'] = endSector

        if self.__hasMultipath:
            part['disk_name'] = '/dev/mapper/%s' % self.__disk

        # extended partition: do not format
        if mtype == 'Ext':
            part['format'] = False

        return part
    # createPartition()

    def createPhysicalVolume(self, disk, size, partition):
        """
        Creates a physical volume partition

        @type  disk: str
        @param disk: disk used to create this partition

        @type  size: int
        @param size: partition size

        @type  partition: str
        @param partition: partition name

        @rtype:   dict
        @returns: physical volume commands
        """
        pv = {}
        pv['command'] = 'create:pv'

        # FIXME: partitioner module only accepts the single name of the disk to
        # create LVM partitions, but when it creates physical partitions, it
        # requires full paths. The right way is configure both cases using the
        # same string
        pv['disk'] = disk.split('/')[-1]

        pv['size'] = size
        pv['partition'] = partition

        return pv
    # createPhisycalVolume()

    def createVolumeGroup(self, pvs, name):
        """
        Creates a volume group partition

        @type  pvs: list
        @param pvs: list of disks in the volume group

        @type  name: str
        @param name: vg name

        @rtype:   dict
        @returns: volume group commands
        """
        vg = {}
        vg['command'] = 'create:volgroup'
        vg['extentSize'] = EXTENT_SIZE
        vg['pvs'] = pvs
        vg['name'] = name

        return vg
    # createVolumeGroup()

    def setDisk(self, disk):
        """
        Sets the disk id.

        @type  size: str
        @param size: disk to be formatted

        @rtype:   nothing
        @returns: nothing
        """
        self.__disk = disk
    # setDisk()

    def setDiskId(self, diskId):
        """
        Sets the disk id.

        @type  size: str
        @param size: disk id

        @rtype:   nothing
        @returns: nothing
        """
        self.__diskId = diskId
    # setDiskId()

    def setDiskSize(self, size):
        """
        Sets the disk size.

        @type  size: int
        @param size: total space in disk, in bytes

        @rtype:   nothing
        @returns: nothing
        """
        # remove 1Mb from total size for safety
        value = size - (1024 * 1024)
        self.__diskSize = value / 1024
    # setDiskSize()

    def setMultipathMode(self, mode):
        """
        Configures a flag to indicate if the system has multipath or not.

        @type  mode: bool
        @param mode: True if the system has multipath, False otherwise

        @rtype: None
        @return: Nothing
        """
        self.__hasMultipath = mode
    # setMultipathMode()

# PartitionCommand
