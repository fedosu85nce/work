#
# IMPORTS
#
from zkvmutils import getstatusoutput
from zkvmutils import lecho
from zkvmutils import llecho
from zkvmutils import run

from controller.zkvmerror import ZKVMError

import cPickle
import fcntl
import glob
import os
import re
import select
import sys
import time


#
# CONSTANTS AND DEFINITIONS
#
CMD_CREATE_RAID_SPARES = 'mdadm --create --metadata=%(metadata)s --run --verbose /dev/%(name)s --level=%(level)d --chunk=%(chunkSize)d --raid-devices=%(nDevices)d --spare-devices=%(nSpares)d %(devices)s'
CMD_CREATE_RAID_NO_SPARES = 'mdadm --create --metadata=%(metadata)s --run --verbose /dev/%(name)s --level=%(level)d --chunk=%(chunkSize)d --raid-devices=%(nDevices)d %(devices)s'
CMD_SET_PART_TYPE = 'sfdisk -c /dev/%(device)s %(number)s fd'
CMD_START_MDADM = 'mdadm --assemble --scan'
CMD_STOP_MDADM = 'mdadm --stop --scan'
CMD_STOP_RAID = 'mdadm --stop --verbose /dev/%(name)s'
CMD_UMOUNT_RAID = 'grep /dev/%(name)s /proc/mounts && umount /dev/%(name)s'
CMD_ZERO_RAID = 'mdadm --zero-superblock --verbose %(devices)s'

CMD_CREATE_RAID = {
    0: CMD_CREATE_RAID_NO_SPARES,
    1: CMD_CREATE_RAID_SPARES,
    5: CMD_CREATE_RAID_SPARES,
}

PATH_MD_CLEAN = '/sys/block/%s/md/array_state'
PATH_MD_COMPLETED = '/sys/block/%s/md/sync_completed'
PATH_MD_DEGRADED = '/sys/block/%s/md/degraded'
PATH_MD_RECOVERY = '/sys/block/%s/md/sync_action'
PATH_MD_SPEED = '/sys/block/%s/md/sync_speed'

PATTERN_PART = re.compile('(?P<device>[_a-zA-Z]+)(?P<number>[0-9]+)')
PATTERN_RAID_SYSFS = '/sys/block/md*'

TABLE = {}


#
# CODE
#
def _create(cmd):
    """
    Creates a RAID array as specified in the passed command

    @type  cmd: dict
    @param cmd: command to be performed

    @rtype: None
    @returns: nothing
    """
    # report the operation
    llecho('Creating RAID level %(level)d array /dev/%(name)s from %(devices)s' % cmd)

    # FIXME: stop raid before any attempt to create an array to assure
    # that there will not be any blocked device causing error
    stop()

    # build command line to be used to create the array
    cmdLine = CMD_CREATE_RAID[cmd['level']] % {
        'name': cmd['name'],
        'level': cmd['level'],
        'chunkSize': cmd['chunkSize'],
        'nDevices': len(cmd['devices']) - cmd['spares'],
        'nSpares': cmd['spares'],
        'devices': ' '.join(['/dev/%s' % d for d in cmd['devices']]),
        'metadata': cmd['metadata'],
    }

    # failed creating the array: exit
    status = run(cmdLine)

    if status != 0:
        llecho('Error: cannot create the array')
        sys.exit(1)

    # FIXME: start raid again after the command was performed
    # successfully
    start()

    # set the partition type of each device as FD
    for device in cmd['devices']:
        _setPartType(device)

    # reiserfs type not chosen on a RAID 0: make a filesystem on this array
    if cmd['fileSystem'] not in ['reiserfs', 'swap']:
        llecho('Creating filesystem of type %(fileSystem)s on /dev/%(name)s - RAID %(level)d' % cmd)
        run('mkfs\.%(fileSystem)s /dev/%(name)s' % cmd)
# _create()

def _delete(cmd):
    """
    Deletes a RAID array as specified in the passed command

    @type  cmd: dict
    @param cmd: command to be performed

    @rtype: None
    @returns: nothing
    """
    # report the operation
    llecho('Deleting RAID array /dev/%(name)s' % cmd)

    # umount the raid partition
    run(CMD_UMOUNT_RAID % cmd)

    # failed stopping the array: report and exit
    status = run(CMD_STOP_RAID % cmd)

    if status != 0:
        llecho('Error: cannot stop the array')
        sys.exit(1)

    # failed zeroing the superblock of the raid devices: report and exit
    status = run(CMD_ZERO_RAID % {
        'devices': ' '.join(['/dev/%s' % d for d in cmd['devices']]),
    })

    if status != 0:
        llecho('Error: cannot zero the superblocks of the RAID devices')
        sys.exit(1)
# _delete()

def _openFiles(md):
    """
    Open files for the passed md device

    @type  md: basestring
    @param md: md device whoses files are to be opened

    @rtype: dict
    @returns: file objects opened
    """
    return {
        'clean': open(PATH_MD_CLEAN % md, 'r'),
        'completed': open(PATH_MD_COMPLETED % md, 'r'),
        'degraded': open(PATH_MD_DEGRADED % md, 'r'),
        'recovery': open(PATH_MD_RECOVERY % md, 'r'),
        'speed': open(PATH_MD_SPEED % md, 'r'),
    }
# _openFiles()

def _poll(files, interval = 0.1, timeout = None):
    """
    Monitors the passed files until at least one of them has been modified and
    returns the modified ones. Checks the files every passed interval. If a
    timeout is passed, waits for at most that time before returning.

    @type  files: list
    @param files: files to be checked

    @type  interval: float
    @param interval: check interval

    @type  timeout: float
    @param timeout: maximum time to wait before returning

    @rtype: set
    @returns: files that have been modified
    """
    # ensure all passed files are on the table
    for fobj in files:
        if fobj.name not in TABLE:
            TABLE[fobj.name] = None

    # monitor them
    modified = set()
    elapsed = 0

    while True:

        # build list of modified files
        for fobj in files:
            data = _read(fobj)

            # file changed: add it to list
            if data != TABLE[fobj.name]:
                TABLE[fobj.name] = data
                modified.add(fobj)

        # there are modified files: done
        if len(modified) > 0:
            break

        # timeout: done
        if timeout != None and elapsed >= timeout:
            break

        # wait before checking again
        time.sleep(interval)
        elapsed += interval

    return modified
# _poll()

def _read(stream):
    """
    Reads all data from the passed file object and rewinds it before returning

    @type  stream: file
    @param stream: file object to be read

    @rtype: basestring
    @returns: data read
    """
    data = stream.read()
    stream.seek(0)
    return data
# _read()

def _readFiles(files, status):
    """
    Reads passed files and writes their data at the passed status dictionary

    @type  files: dict
    @param files: files to be read

    @type  status: dict
    @param status: place to write the data read from the files

    @rtype: dict
    @returns: file objects opened
    """
    for name, fo in files.iteritems():
        status[name] = fo.read().strip()
        fo.seek(0)
# _readFiles()

def _setPartType(device):
    """
    Sets the partition type of the passed device as linux_raid_auto

    @type  devices: basestring
    @param devices: device whose partition type is to be set

    @rtype: None
    @returns: nothing
    """
    # report the operation
    llecho('Setting the partition type of %s as linux_raid_auto' % device)

    # not a valid device name: error
    match = PATTERN_PART.match(device)

    if match == None:
        llecho('Error: cannot parse %s into a device name '
              'and partition number' % device)
        sys.exit(1)

    # get device name and partition number
    info = match.groupdict()

    # cannot set partition type: error
    status = run(CMD_SET_PART_TYPE % info)

    if status != 0:
        llecho('Error: cannot set the partition type of '
              '/dev/%(device)s Id %(number)s' % info)
        sys.exit(1)
# _setPartType()

def createArrays(commands):
    """
    Processes RAID operations as specified by the passed list of commands and
    performs the ones which create RAID arrays

    @type  commands: list
    @param commands: list of commands to be processed

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Creating RAID arrays')

    # create raid arrays
    for cmd in commands:
        if cmd['command'] == 'create:raid':
            _create(cmd)
# createArrays()

def deleteArrays(commands):
    """
    Processes RAID operations as specified by the passed list of commands and
    performs the ones which delete RAID arrays

    @type  commands: list
    @param commands: list of commands to be processed

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Deleting RAID arrays')

    # delete raid arrays
    for cmd in commands:
        if cmd['command'] == 'delete:raid':
            _delete(cmd)
# deleteArrays()

def loadCommands(path):
    """
    Loads from the pickle file at the passed path RAID operations to be
    performed

    @type  path: basestring
    @param path: path of the pickle file to be loaded

    @rtype: dict
    @returns: RAID operations to be performed
    """
    # report operation
    llecho('Loading RAID operations to be performed')

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
    except:
        llecho('Error: cannot load list of operations to be done')
        sys.exit(1)

    return commands
# loadCommands()

def start():
    """
    Activate all existing RAID arrays so that RAID operations can be performed

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Activating all existing RAID arrays')

    # failed creating the array: exit
    status = run(CMD_START_MDADM)

    if status != 0 and status != 1:
        llecho('Error: cannot activate RAID arrays')
        sys.exit(1)
# start()

def stop():
    """
    Stops all RAID arrays so that all resources (partitions) are released and
    disks partitioning can be done

    FIXME: There is a know bug (73870) that happens when installing an
    automatic partitioning scheme after a previous RAID parition in multiple
    disks. It was added a loop with a sleep trying to stop until 10 times if
    it fails. A better solution should be investigated here.

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Stopping all RAID arrays')

    # stop the raid device
    status = 0

    for i in range(0, 10):
        # run the command to stop raid
        status = run(CMD_STOP_MDADM)

        # raid stopped successfully: quit
        if status == 0:
            break

        # wait 1 second before another try
        time.sleep(1)

    # problems to stop raid: exit -1
    if status != 0:
        llecho('Error: cannot stop RAID arrays')
        raise ZKVMError('PARTITIONER', 'RAID', 'STOP_SWRAID')
# stop()

def wait(commands):
    """
    Processes RAID operations as specified by the passed list of commands and
    waits for the RAID arrays set to be created and reused to become clean. An
    array is not clean when, for example, it has just been created and its
    spares are synching.

    @type  commands: list
    @param commands: list of commands to be processed

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Waiting for RAID arrays to become clean')

    # get RAID arrays to be monitored
    mds = []

    for cmd in commands:

        # created or reused array: monitor it
        if cmd['command'] in ('create:raid', 'use:raid'):

            # level 0 array: no need to monitor
            if cmd['level'] != 0:
                mds.append(cmd['name'])

    # show arrays
    llecho('Arrays: %s' % mds)

    # open file objects for each array
    files = {}

    for md in mds:
        files[md] = _openFiles(md)

    # get descriptors for the files to be monitored
    mdsByFd = {}
    status = {}
    names = {}

    for md, fobjs in files.iteritems():
        fd = fobjs['completed']
        mdsByFd[fd] = fobjs
        status[fd] = {}
        names[fd] = md

    fds = mdsByFd.keys()

    # monitor arrays until all are clean
    while True:
        r = _poll(fds, interval = 0.5, timeout = 1.0)

        # read files for the mds with data available
        for fd in r:
            _readFiles(mdsByFd[fd], status[fd])

            # md finished sync: stop monitoring it
            if status[fd]['recovery'] == 'idle':
                llecho('Array /dev/%s is clean' % names[fd])
                fds.remove(fd)

        # no more mds to be monitored: done
        if len(fds) == 0:
            break
# wait()
