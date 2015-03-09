#
# IMPORTS
#
from operator import itemgetter
from zkvmutils import getstatusoutput
from zkvmutils import lecho
from zkvmutils import llecho
from zkvmutils import run

import time

import cPickle
import manage_raid as raid
import os
import re
import sys


#
# CONSTANTS AND DEFINITIONS
#

# commands
CMD_CHECK_PARTITION = 'blkid -p -u filesystem -o value -s PTTYPE %(disk)s'
CMD_CREATE_PARTITION = 'parted --script --align optimal %(disk_name)s unit s mkpart %(type)s %(start)s %(end)s'
CMD_DELETE_PARTITION = 'parted --script %(disk_name)s rm %(nr)s'
CMD_FIX_DISK_LABEL = 'parted --script %(disk)s mklabel msdos'
CMD_HDPARM_Z = 'hdparm -z %s'
CMD_LIST_ALL = 'parted -sl'
CMD_SET_PARTITION_FLAG = 'parted --script %(disk_name)s set %(nr)d %(flag)s %(state)s'

# error messages
ERROR_CREATE = 'Error: cannot create partition %(name)s'
ERROR_DELETE = 'Error: cannot delete partition %(name)s'
ERROR_FIX = 'Error: cannot fix disk label of %s'
ERROR_FLAG = 'Error: cannot change flag %(flag)s of partition %(name)s'

# parted input migration
DEVICE_PATH = '/dev/%(disk_name)s'
MPATH_PATH = '/dev/mapper/%(disk_name)s'

TYPE = {
    'Pri': 'primary',
    'Ext': 'extended',
    'Log': 'logical',
}

# max number of partition table synchronization attempts
MAX_SYNC_ATTEMPTS = 20

#
# CODE
#
def adjustCommandsToParted(commands):
    """
    Adjusts commands to use 'parted' tool expected inputs.

    @type  commands: list
    @param commands: Conventional Disk operations to be performed

    @rtype: list
    @returns: disk operations using parted command expected input
    """
    # report operation
    llecho('Adjusting conventional disk operations to be used by parted command')

    # update commands
    for command in commands:

        # update disk name to use full path
        if command['mpath_master'] is not None:
            command['disk_name'] = MPATH_PATH % command
        else:
            command['disk_name'] = DEVICE_PATH % command

        # command has partition type: update it
        if 'type' in command:
            command['type'] = TYPE[command['type']]

# adjustCommandsToParted()

def _fixDiskLabel(device):
    """
    Fixes disk label so it can be properly partitioned afterwards.

    @type  device: basestring
    @param device: passed device (e.g. '/dev/sda', '/dev/sdb', ...)

    @rtype: None
    @returns: Nothing
    """
    # disk label could not be fixed: report error
    status = run(CMD_FIX_DISK_LABEL % {'disk': device})

    if status != 0:
        llecho(ERROR_FIX % device)
        sys.exit(1)

    # partition table was reset: report operation
    llecho('Partition table for %s was reset' % device)
# _fixDiskLabel()

def _getModifiedDisks(diskCommands):
    """
    Gets from the list of commands the set of disks that will be modified.

    @type  diskCommands: dict
    @param diskCommands: abstract commands for conventional disks

    @rtype: set
    @returns: set of disk names
    """

    # get set of disks that will be modified
    disks = set()

    for cmd in diskCommands:

        # disk will be modified: add to set
        if cmd['command'] in ['create:partition', 'delete:partition']:
            disks.add(cmd['disk_name'])

    return disks
# _getModifiedDisks()

def _hasValidDiskLabel(disk):
    """
    Informs if the disk has a valid disk label.

    @type  disk: basestring
    @param disk: disk path

    @rtype: bool
    @returns: True if the disk has a valid label, False otherwise
    """
    # get disk label through blkid
    (status, output) = getstatusoutput(CMD_CHECK_PARTITION % {'disk': disk})

    # could not get disk label or it is invalid: return False
    if status != 0 or output.strip() != 'dos':
        return False

    # valid disk label: return True
    return True
# _hasValidDiskLabel()

def _reReadPartitionTable(disk, hasMultipath = False):
    """
    Asks the kernel to re-read the partition table before trying
    to format it

    @type  disk: basestring
    @param disk: disk device name

    @type  hasMultipath: bool
    @param hasMultipath: info about multipath on machine

    @rtype: bool
    @return: True if partition table sync successfull. False otherwise
    """
    # give some opportunities to sync the partition table before
    # returning false
    for i in range(1, MAX_SYNC_ATTEMPTS):

        # log the number of attempts
        llecho('Re-reading partition table for %s (try %d)' % (disk, i))

        # wait 1 second
        time.sleep(1)

        # FIXME: during the attempt to read the partitions, raid should
        # be inactive or it will block devices belonging to its array
        # and will make the next command to fail. It is not clear why
        # raid becomes active here since is has been stopped in
        # manage_parts. It demands further investigation.
        if hasMultipath:
            raid.stop()

        # partition table re-read successfully: return success
        if run(CMD_HDPARM_Z % disk) == 0:
            return True

    return False
# _reReadPartitionTable()

def _reverseOrderDeleteCommands(diskCommands):
    """
    Select delete commands and reverses the order of the list based on the
    partitions' ids. This is necessary because the parted tool reorder the
    logical partitions when they are removed in order. For example, if you
    remove logical partition 5, 6 will become 5, 7 will become 6 and so on.
    When deleted in reverse order this issue does not happen.

    @type  diskCommands: list
    @param diskCommands: abstract commands for conventional disks

    @rtype: list
    @returns: deletion commands in reverse order
    """

    # select delete partitions commands
    deleteCommands = []

    for cmd in diskCommands:

        # command is delete: copy
        if cmd['command'] == 'delete:partition':
            deleteCommands.append(cmd)

    # reverse the order of the list based on partitions ids
    return sorted(deleteCommands, key=itemgetter('nr'), reverse=True)

# _reverseOrderDeleteCommands()

def _runPartedCommand(partedCommand, disk, errorMessage, hasMultipath=False, tolerant=False):
    """
    Runs a parted command and re-read disk partition table.

    @type  partedCommand: basestring
    @param partedCommand: parted command to run

    @type  disk: basestring
    @param disk: disk path

    @type  errorMessage: basestring
    @param errorMessage: error message to user in case of a failure

    @type  hasMultipath: bool
    @param hasMultipath: flag that informs if system has multipath

    @type  tolerant: bool
    @param tolerant: True to not exit if error found, False otherwise

    @rtype: None
    @returns: nothing
    """
    # runs command
    (status, output) = getstatusoutput(partedCommand)

    # log command line
    llecho("Running: %s" % partedCommand)

    # log exit status and output
    llecho("Status: %d" % status)
    llecho("Output:\n%s\n" % output)

    if hasMultipath:
        return

    # FIXME: use a safer check here, i.e., a regular expression to match the
    # desired output.
    # partition table needs to be re-read: do it
    if 're-read' in output:

        # partition table was successfully re-read: change status accordingly
        if _reReadPartitionTable(disk, hasMultipath):
            status = 0

    # command failed: log and exit
    if status != 0:
        llecho(errorMessage)
        if not tolerant:
            sys.exit(1)
# _runPartedCommand()

def _setFlag(cmd, flag, hasMultipath = False):
    """
    Sets a specific partition's flag as 'on'.

    @type  cmd: dict
    @param cmd: abstract create command for conventional disks

    @type  flag: basestring
    @param flag: flag to be set

    @type  hasMultipath: bool
    @param hasMultipath: info about multipath on machine

    @rtype: None
    @returns: nothing
    """

    # create a copy of cmd
    cmd = cmd.copy()

    # add parameters
    cmd['flag'] = flag
    cmd['state'] = 'on'

    # get parameters to set partition flag
    partedCommand = CMD_SET_PARTITION_FLAG % cmd
    disk = cmd['disk_name']
    errorMessage = ERROR_FLAG % cmd

    # set flag
    _runPartedCommand(partedCommand, disk, errorMessage, hasMultipath)
# _setFlag()

def createPartitions(diskCommands, hasMultipath, sector_size):
    """
    Creates all partitions.

    @type  diskCommands: dict
    @param diskCommands: abstract commands for conventional disks

    @type  hasMultipath: bool
    @param hasMultipath: info about multipath on machine

    @rtype: None
    @returns: Nothing
    """
    # report the operation
    llecho('Creating Partitions')

    # create partitions
    for cmd in diskCommands:

        # command is not create: do nothing
        if cmd['command'] != 'create:partition':
            continue

        # remove any possible LVM garbage from the PVs partition
        llecho('Clear partitions before creating')
        run('dd if=/dev/zero of=%s bs=%d seek=%s count=2048' % (cmd['disk_name'], sector_size, cmd['start']))

        # command is create: report operation and run it
        llecho('Creating partition /dev/%(name)s' % cmd)

        # get parameters to create partition
        cmd['type'] = TYPE[cmd['type']]
        partedCommand = CMD_CREATE_PARTITION % cmd
        disk = cmd['disk_name']
        errorMessage = ERROR_CREATE % cmd

        # create partition
        _runPartedCommand(partedCommand, disk, errorMessage, hasMultipath)

        # partition is PReP: set as bootable
        if cmd['fs'] == 'prep':
            _setFlag(cmd, 'boot', hasMultipath)

        # partition is PReP, RAID or LVM: set respective flag
        if cmd['fs'] in ['prep', 'raid', 'lvm']:
            _setFlag(cmd, cmd['fs'], hasMultipath)

        if cmd['fs'] == 'extended':
            continue

# createPartitions()

def deletePartitions(diskCommands, hasMultipath, tolerant=False):
    """
    Deletes all partitions.

    @type  diskCommands: dict
    @param diskCommands: abstract commands for conventional disks

    @type  hasMultipath: bool
    @param hasMultipath: info about multipath on machine

    @type  tolerant: bool
    @param tolerant: True to not exit if error found, False otherwise

    @rtype: None
    @returns: Nothing
    """
    # report the operation
    llecho('Deleting Partitions')

    # reverse order the list of deletion commands. this is necessary because
    # the parted tool reorder the logical partitions when they are removed in
    # order. for example, if you remove logical partition 5, 6 will become 5, 7
    # will become 6 and so on.
    deleteCommands = _reverseOrderDeleteCommands(diskCommands)

    # delete partitions
    for cmd in deleteCommands:

        # report operation and run it
        llecho('Deleting partition /dev/%(name)s' % cmd)

        # get parameters to delete partition
        partedCommand = CMD_DELETE_PARTITION % cmd
        disk = cmd['disk_name']
        errorMessage = ERROR_DELETE  % cmd

        # delete partition
        _runPartedCommand(partedCommand, disk, errorMessage, hasMultipath, tolerant)
# deletePartitions()

def fixPartitionTables(diskCommands):
    """
    Clear asked disks and checks if the disks that will be modified have valid
    MS-DOS partition tables and fixes them if not.

    @type  diskCommands: dict
    @param diskCommands: abstract commands for conventional disks

    @rtype: None
    @returns: Nothing
    """
    # get disks to be cleared
    disksToBeCleared = set()

    for cmd in diskCommands:

        # command is clear disk: get disk name
        if cmd['command'] == 'clear:disk':
            disksToBeCleared.add(cmd['disk_name'])

    # fix disks that do not have a valid partition table
    for disk in _getModifiedDisks(diskCommands):

        # disk does not have a valid partition table: fix it
        if disk in disksToBeCleared or not _hasValidDiskLabel(disk):
            _fixDiskLabel(disk)
# fixPartitionTables()

def loadCommands(path):
    """
    Loads from the pickle file at the passed path conventional disk operations to be
    performed

    @type  path: basestring
    @param path: path of the pickle file to be loaded

    @rtype: dict
    @returns: Conventional Disk operations to be performed
    """
    # report operation
    llecho('Loading Conventional disk operations to be performed')

    # cannot locate list of commands to be processed: report and exit
    if os.path.exists(path) == False:
        llecho('Error: cannot locate list of operations to be done')
        sys.exit(1)

    # load the list of commands
    try:
        stream = open(path)
        commands = cPickle.load(stream)
        stream.close()

    # loading error: report and exit
    except (EnvironmentError, cPickle.PickleError):
        llecho('Error: cannot load list of operations to be done')
        sys.exit(1)

    # adjust commands to be used by parted
    adjustCommandsToParted(commands)

    # return loaded commands
    return commands
# loadCommands()

def logPartitioningScheme():
    """
    Logs all disks state

    @rtype: tuple
    @returns: (status, output) of command
    """
    return getstatusoutput(CMD_LIST_ALL)
# logPartitioningScheme()
