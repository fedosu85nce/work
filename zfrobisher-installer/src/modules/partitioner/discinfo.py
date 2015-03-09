#
# IMPORTS
#
from copy import deepcopy

import lvminfo
import os
import raidinfo
import re
import time


#
# CONSTANTS AND DEFINITIONS
#
__all__ = [ "get_hierarchy_physical" ]

BLOCK_SIZE = 1024
NOTMOUNT = ("swap", "lvm", "raid", "unknown", "prep", "extended")
EXTENDED_PARTS = ('5', 'f', '85')
MPATH_FIND_DM = 'dmsetup info -c --noheadings -o minor /dev/mapper/%s 2>/dev/null'
SYS_DM_PATH = '/sys/block/dm-%s/slaves/'
GET_DISK_ID = "udevadm info --query=symlink --name %s | grep -o 'disk/by-id/[[:alnum:][:punct:]]*'"


#
# CODE
#
def check_device(disk):
    """
    Check if a disk can be read successfully

    @type  disk: basestring
    @param disk: disk name (sda, sdb, etc)

    @rtype: bool
    @return: True if success, False if any problem happened such as Buffer I/O
    """
    # try to read a byte from the device
    try:
        # read the MBR signature, bytes 511 and 512
        stream = open('/dev/%s' % disk, 'r')
        stream.read(1)
        stream.close()

    # impossible to read the disk: return False
    except IOError:
        return False

    # problems with permissions: return False
    except OSError:
        return False

    return True
# check_device()

def detect_partition_table_type(name, default = None):
    """
    Detects and returns the partition table type of the disk with the passed
    name. If the detection fails, returns the passed default value. Currently,
    the only supported partition type is 'msdos'.

    @type  device: basestring
    @param device: passded disk name (e.g. 'sda', 'sdb', ...)

    @type  default: arbitrary
    @param default: default value to be returned

    @rtype: basestring or None
    @returns: detected partition table type, or default
    """
    # try to read the 511/512 bytes of a disk
    try:
        # read the MBR signature, bytes 511 and 512
        stream = open('/dev/%s' % name, 'r')
        stream.seek(510)
        data = stream.read(2)
        stream.close()

    # impossible to read the disk: return default
    except IOError:
        return default

    # permissions issues: return default
    except OSError:
        return default

    # MS-DOS partition table signature (0xAA55): return it
    if ord(data[0]) == 0x55 and ord(data[1]) == 0xAA:
        return 'msdos'

    # unknown partition: return the default value
    return default
# detect_partition_table_type()

def detect_multipath_scheme():
    """
    Detects an return the multipath scheme of the system.

    @rtype: dictionary
    @returns: a dictionary with the multipath masters as key and the values
              are a list of strings of the slaves names.
    """
    # turn on multipath
    run_multipath('multipath -F', 1.0)
    run_multipath('multipath -r', 1.0)

    # get the master names
    masters = run_multipath('multipath -l -v1').split()

    # get all its slaves and build topology
    topology = {}

    for master in masters:

        # not a mpath device: get next
        if not 'mpath' in master or '/' in master:
            continue

        # get device mapper id
        stream = os.popen(MPATH_FIND_DM % master)
        mpathDm = stream.read().strip()
        status = stream.close() or 0

        # no valid device mapper id: skip
        if status != 0:
            continue

        # get slaves of this device mapper
        topology[master] = os.listdir(SYS_DM_PATH % mpathDm)

    # return the topology
    return topology
# detect_multipath_scheme()

def get_disk_id(diskName, default = None):
    """
    Return the unique identifier of the disk

    @type  diskName: basestring
    @param diskName: disk name, ex: 'sda'

    @type  default: arbitrary
    @param default: default value to be returned

    @rtype:   string
    @returns: disk id, ex: /dev/disk/by-id/.
    """
    # get id by udevadm
    command = os.popen(GET_DISK_ID % diskName)
    id = command.readline()

    # command did not return in disk/by-id format: return default
    if "disk/by-id" not in id:
        return default

    # remove break lines and return
    return '/dev/' + id.replace("\n","")
# get_disk_id()

def get_disk_size(disk, default = None):
    """
    Returns the size of the passed disk. If it cannot be determined,
    returns the passed default value.

    @type  disk: basestring
    @param disk: disk name ('sda', 'sdb', ...)

    @type  default: arbitrary
    @param default: default value to be returned

    @rtype: int
    @returns: disk size in bytes
    """
    # read the sector size from sysfs
    stream = os.popen('sfdisk -s /dev/%s 2>/dev/null' % disk)
    data = stream.read().strip()
    stream.close()

    # convert it to int and return
    try:
        return int(data) * BLOCK_SIZE

    # not a number: return the default value
    except:
        return default
# get_disk_size()

def get_multipath_info(name, multipaths):
    """
    Given the passed multipath topology, returns the multipath master and
    sibling slaves for the device with the passed name. If they do not exist,
    returns None for the multipath master and an empty list of the slaves.

    @type  name: basestring
    @param name: name of the device

    @type  multipaths: dict
    @param multipaths: multipath topology to be used

    @rtype: tuple
    @returns: multipath master and slaves
    """
    # master and slaves found: return them
    for master in multipaths:
        if name in multipaths[master]:
            return master, multipaths[master]

    # return fallback values
    return None, []
# get_multipath_info()

def new_disk(disks, name, size, type, sectorSize, master, slaves, id):
    # invalid list of disks: fail
    if disks is None:
        return False

    # create the dictionary with info about the disk
    disk = {}
    disk['name'] = name
    disk['size'] = size
    disk['parts'] = []
    disk['non_part_space'] = size
    disk['touched'] = False
    disk['reuse'] = False
    disk['avail_space'] = 0
    disk['type'] = type
    disk['sectorSize'] = sectorSize
    disk['mpath_master'] = master
    disk['mpath_slaves'] = slaves
    disk['id'] =  id
    disk['accessible'] = check_device(name)

    # append it to the list of disks
    disks.append(disk)
# new_disk()

def new_part(disk, instance, free, fstype, ptype):
    if disk is None:
        return False

    part = deepcopy(instance)
    if part.has_key('name'):
        if ptype == 'E':
            part['size'] = 1
        disk['non_part_space'] -= part['size']
        part['nr'] = int(re.search('(\d+)$', part['name']).group(1))
    else:
        part['end'] = part['start'] + part['size'] - 1
        part['id'] = '0'
        part['name'] = 'empty'
        disk['avail_space'] += part['size']
        part['nr'] = 0
    part['format'] = 'no'
    part['mount_point'] = ''
    part['type'] = ptype
    part['free'] = free
    part['fs'] = fstype
    disk['parts'].append(part)

    return True
# new_part()

def add_parts(disk, partConf):
    parts = partConf['primaryParts']
    spaces = partConf['emptySpaces']
    for part in partConf['extendedParts']:
        parts.extend(part['childParts'])
        spaces.extend(part['emptySpaces'])

    for part in parts:
        if 'mpath' in part['name']:
            # The device-mapper names on MCP6.1 prefix the partition number
            # with "_part". Not adding it caused get_part_free_space to fail
            # since the device /dev/mapper/mpath<ID><NUMER> never exists.
            new_name = re.sub(r"(mpath.)(\d)", r"\1_part\2", part['name'])
            part['name'] = new_name
        try:
            # get filesystem type
            fstype = get_fstype(part)

            # get partition type
            ptype = get_ptype(part['name'], fstype)

            # get free space in partition
            free = get_part_free_space(part['name'], fstype, partConf['sectorSize'])
        except:
            # we are here possibly because of an usb floppy from hell. Just ignore it
            continue

        if ptype == 'E':
            size = 1
        else:
            size = part['size']
        new_part(disk, part, free, fstype, ptype)

    for space in spaces:
        if space['size'] / 2 > 1024:
            new_part(disk, space, space['size'], '', '')
# add_parts()

def get_partition_lines():
    entries = []

    # read partitions file and get its lines
    fin = open('/proc/partitions')
    lines = fin.readlines()
    fin.close()

    for l in lines:
        # split line into its four fields
        e = l.strip().split()

        # store only adequate entries (with hd* and sd*)
        if len(e) >= 4:
            if 'hd' in e[3] or 'sd' in e[3]:
                entries.append(e)
    return entries
# get_partition_lines()

def is_removable(name):
    # Verify whether our disk is removable
    # If it is, skip it
    path = os.path.join('/sys/block', name)
    try:
        f = open(os.path.join(path, 'removable'))
        line = f.readline()
        f.close()
    except:
        return False

    if int(line.strip()):
        return True

    return False
# is_removable()

def get_ptype(name, fstype):
    # get partition type
    # Warning: throws IndexError if the input is invalid
    partno = int(re.search(r'(\d+)$', name).group(1))
    if partno > 4:
        ptype = 'L'
    elif fstype == 'extended':
        ptype = 'E'
    else:
        ptype = 'P'
    return ptype
# get_ptype()

def get_part_free_space(name, fstype, sectorSize):
    if fstype not in NOTMOUNT:
        # mount the partition at /tmp/mnt
        cmdLine = "mount -t %s /dev/%s /tmp/mnt 2>/dev/null" % (fstype, name)
        os.system(cmdLine)

        # Use 'df' to retrieve the used space
        cmdLine = "df --block-size %d /tmp/mnt" % sectorSize
        pipe = os.popen(cmdLine)
        partData = pipe.read()
        free = int(partData.strip().split()[-3])
        pipe.close()
        os.system("umount /tmp/mnt 2>/dev/null")
    else:
        free = -1

    return free
# get_part_free_space()

def get_fstype(part):
    # first let's see if this is either a PReP or a LVM
    if part['id'].lower() == '8e':
        fstype = 'lvm'
    elif part['id'].lower() == 'fd':
        fstype = 'raid'
    elif part['id'] in ('41', '6') and part['size'] < (2 * 32 * 1024):
        fstype = 'prep'
    elif part['id'] in ('5', 'f', '85'):
        fstype = 'extended'
    # no, so we need to find out using blikid
    else:
        cmdLine = "blkid /dev/%s" % (part['name'])
        pipe = os.popen(cmdLine)
        blkidOut = pipe.read().strip()
        pipe.close()

        if blkidOut != '':
            fstype = blkidOut.split(' TYPE=')[1].split()[0].strip('"')
        else:
            fstype = "unknown"
        # workaround to fix swap detection in some systems
        if 'swap' in fstype:
            fstype = 'swap'

    return fstype
# get_fstype()

def isSAN(disk):
    """
    Checks if the disk is a fibre-channel.

    @type  disk: str
    @param disk: disk name

    @rtype:   bool
    @returns: True if is fibre-channel
    """
    if not disk:
        return None

    # remove the path and get only the disk name
    diskname = disk.split('/')[-1]
    
    # doesnt handle mpath, the caller must pass any of
    # its slave if want verify mpath
    if 'mpath' in diskname:
        return None

    # remove any partition numbers from the diskpath
    diskname = diskname.translate(None, '0123456789')

    # get the full device path
    linkpath = '/sys/block/%s' % diskname
    realpath = os.path.realpath(linkpath)

    # realpath should not be the same because we
    # need the san disk path in order to verify if
    # it's fibre-channel
    if realpath == linkpath:
        return None

    # as per udev (udev-builtin-path_id.c), rport means the disk
    # is a fibre-channel
    if '/rport-' in realpath:
        return True

    return False
# isSAN()

def isNumber(c):
    """
    Checks if a given character is an int

    @rtype: bool
    @returns: True is c is a number, False otherwise
    """
    try:
        int(c)
        return True
    except ValueError:
        return False
# isNumber()

def get_hierarchy_physical(use_multipath=False):
    # create a temp dir to mount the partitions in order to determine their free space
    try:
        os.mkdir("/tmp/mnt")
    except OSError:
        os.system("umount /tmp/mnt 2>/dev/null")

    # parse lines
    entries = get_partition_lines()

    # detect the multipath topology for this machine
    multipaths = detect_multipath_scheme()

    # build disk hierarchy from the entries
    disks = []

    for e in entries:
        name = e[3]

        # check if is a valid disk (not a partition)
        if len(name) > 2 and (name[:2] == 'sd' or name[:4] == 'dasd') and not isNumber(name[-1:]):

            # if this disk is removable, skip it
            if is_removable(name):
                continue

            # detect the partition table type of this disk
            type = detect_partition_table_type(name)

            # get multipath info for the device
            master, slaves = get_multipath_info(name, multipaths)

            # get disk id
            id = get_disk_id(name)

            # FIXME: sfdisk is always returning 512 bytes as the
            # sector size for a disk.  Even on 4k disks, it's
            # returning 512 bytes.  It's a bug!  To workaround that,
            # we always use sector size from get_sector_size() which
            # reads value from /sys/block/<dev>/queue/physical_block_size.
            sector_size = get_sector_size(name)

            # non-msdos partition table: cannot read partitions, add empty disk
            if type != 'msdos':
                size = get_disk_size(name) / sector_size
                new_disk(disks, name, size, type, sector_size, master, slaves, id)
                empty = {'start': 1, 'size': size - 1}
                new_part(disks[-1], empty, size, '', '')
                continue

            # msdos but could not read partitions: ignore disk
            partConf = parseParts(name)

            if not isinstance(partConf, dict):
                continue

            # append new disk
            new_disk(disks, name, partConf['diskSize'], type, sector_size,
                     master, slaves, id)
            disk = disks[-1]

            # append disk partitions
            add_parts(disk, partConf)

    # now let's sort the partitions in our list based upon their actual position on the disks
    for d in disks:
        if len(d['parts']) > 0:
            d['parts'].sort(lambda x, y: x['start'] - y['start'])

    return disks
# get_hierarchy_physical()

def get_hierarchy_lvm(physical):
    """
    Updates the disks hierarchy with info about LVM entities present in it

    @type  physical: dict
    @param physical: disks hierarchy

    @rtype: dict
    @returns: lvm hierarchy
    """
    # get LVM hierarchy
    lvm = lvminfo.getHierarchy()

    # set the physical disks and partitions
    get_lvm_entities(physical, lvm)

    return lvm
# get_hierarchy_lvm()

def get_hierarchy_raid(physical):
    """
    Updates the disks hierarchy with info about RAID entities present in it

    @type  physical: list
    @param physical: disks hierarchy as returned by L{get_hierarchy}

    @rtype: dict
    @returns: raid hierarchy
    """
    # get RAID hierarchy
    raid = raidinfo.getHierarchy()

    # set the physical disks and partitions
    get_raid_entities(physical, raid)

    return raid
# get_hierarchy_raid()

def get_lvm_entities(hierarchy, lvm_info):
    """
    Updates the disks hierarchy with info about LVM entities present in it

    @type  hierarchy: dict
    @param hierarchy: disks hierarchy

    @rtype: None
    @returns: nothing
    """
    # flag LVM disks and partitions
    pvs = lvm_info['pvs']

    for disk in hierarchy:
        # whole disk is a LVM physical volume: flag it so and move on
        if disk['name'] in pvs:
            disk['type'] = 'lvm'
            continue

        for part in disk['parts']:
            # partition is a LVM physical volume: flag it so
            if part['name'] in pvs:
                part['fs'] = 'lvm'
                part['free'] = -1
# get_lvm_entities()

def get_raid_entities(hierarchy, raidInfo):
    """
    Updates the disks hierarchy with info about raid entities present in it

    @type  hierarchy: list
    @param hierarchy: disks hierarchy as returned by L{get_hierarchy}

    @type  raidInfo: dict
    @param raidInfo: raid hierarchy

    @rtype: None
    @returns: nothing
    """
    # flatten all the physical disks used by raid
    allRaidPartsUsed = set([part
            for md in raidInfo.itervalues()
                for part in md['devices']])

    # flag all partitions used in RAID
    for disk in hierarchy:
        for part in disk['parts']:

            # partition is a raid physical volume: flag it so
            if part['name'] in allRaidPartsUsed:
                part['fs'] = 'raid'
                part['free'] = -1
# get_raid_entities()

def get_sector_size(disk, default = 512):
    """
    Returns the sector size of the passed disk. If it cannot be determined,
    returns the passed default value.

    @type  disk: basestring
    @param disk: disk name ('sda', 'sdb', ...)

    @type  default: arbitrary
    @param default: default value to be returned

    @rtype: int
    @returns: sector size in bytes
    """
    # read the sector size from sysfs
    stream = open('/sys/block/%s/queue/logical_block_size' % disk, 'r')
    data = stream.read().strip()
    stream.close()

    # convert it to int and return
    try:
        return int(data)

    # not a number: return the default value
    except:
        return default
# get_sector_size()

def parseParts(disk_name):

    disk = '/dev/%s' % disk_name

    partConf = {}
    partConf['headers'] = []
    partConf['primaryParts'] = []
    partConf['emptyParts'] = []
    partConf['extendedParts'] = []
    partConf['allParts'] = []

    # Dump partitions
    pipe = os.popen('sfdisk -dx %s 2>/dev/null' % disk)
    dump = pipe.read().strip()
    if pipe.close() != None:
        return 'Error running sfdisk command'

    # Determine disk size in sectors
    # First, determine block size
    pipe = os.popen('sfdisk -l -uB %s 2>/dev/null' % disk)
    output = pipe.readlines()
    pipe.close()
    blockSize = 0
    for line in output:
        if line.startswith('Units') and line.find('blocks of ') > -1:
            try:
                blockSize = int(line.split('blocks of ')[1].split()[0])
            except:
                return 'Error determining disk block size'
            break
    if blockSize == 0:
        return 'Could not determine disk block size'
    # Determine sector size
    sectorSize = get_sector_size(disk_name)
    if sectorSize == 0:
        return 'Could not determine disk sector size'
    partConf['sectorSize'] = sectorSize
    # Now, do the math
    pipe = os.popen('sfdisk -s %s' % disk)
    output = pipe.read().strip()
    pipe.close()
    try:
        diskBlocks = int(output)
        partConf['diskSize'] = int((diskBlocks * blockSize) / sectorSize)
    except:
        return 'Error determining disk size'

    # Add each partition to the list
    dump = dump.split('\n')
    saveHeader = True
    i = 0
    while i < len(dump):
        line = dump[i]
        i = i + 1
        # not a partition line: save as header or discard
        if not line.startswith('/dev/'):
            if saveHeader:
                partConf['headers'].append(line)
            continue
        saveHeader = False

        try:
            fields = line.split()
            name = line.split()[0].strip('/dev/').strip(':')
            start = int(line.split('start=')[1].split(',')[0].strip())
            size = int(line.split('size=')[1].split(',')[0].strip())
            id = line.split('Id=')[1].split(',')[0].strip()
            number = int(re.search('(\d+)$', name).group(1))
        except:
            return 'Error retrieving values from sfdisk dump'

        end = start + size - 1
        part = { 'name': name, 'start': start, 'end': end, 'size': size,
                'id': id, 'nr': number}

        # partition is logical
        if part['nr'] > 4:
            # we need to store the next logical partition info
            nextLine = dump[i]
            i = i + 3
            try:
                part['nextStart'] = int(nextLine.split('start=')[1].split(',')[0].strip())
                part['nextSize'] = int(nextLine.split('size=')[1].split(',')[0].strip())
                part['nextId'] = nextLine.split('Id=')[1].split(',')[0].strip()
            except:
                return 'Error retrieving values from sfdisk dump'

        # Add to appropriate list. At this moment we are possibly
        # adding to the primary list a partition that is inside an extended
        # one, but it will be removed at the second step when the extended
        # list is complete.
        if id == '0':
            partConf['emptyParts'].append(part)
        else:
            partConf['primaryParts'].append(part)
            # partition is extended; also save in appropriate list
            if id in EXTENDED_PARTS:
                extPart = part.copy()
                extPart['childParts'] = []
                partConf['extendedParts'].append(extPart)

        partConf['allParts'].append(part)

    # Now move all partitions inside an extended partition to the extended list
    for part in partConf['primaryParts'][:]:
        for i in range (0, len(partConf['extendedParts'])):
            # partition is inside extended: move to list
            if part['start'] > partConf['extendedParts'][i]['start'] \
                and part['end'] <= partConf['extendedParts'][i]['end']:
                partConf['primaryParts'].remove(part)
                partConf['extendedParts'][i]['childParts'].append(part)

    # Order partitions by position on disk
    partConf['primaryParts'].sort(lambda x, y: cmp(x['start'], y['start']))
    partConf['extendedParts'].sort(lambda x, y: cmp(x['start'], y['start']))
    for i in range (0, len(partConf['extendedParts'])):
        partConf['extendedParts'][i]['childParts'].sort(lambda x, y: cmp(x['start'], y['start']))
    # Order empty and all partitions by name
    partConf['emptyParts'].sort(lambda x, y: cmp(x['nr'], y['nr']))
    partConf['allParts'].sort(lambda x, y: cmp(x['nr'], y['nr']))

    # Find empty spaces between primary partitions
    partConf['emptySpaces'] = []

    # No primary parts: add entire space
    if len(partConf['primaryParts']) == 0:
        spaceDict = {
            'start': 1,
            'size': partConf['diskSize'] - 1
        }
        partConf['emptySpaces'].append(spaceDict)
    else:
        # check disk beginning
        if partConf['primaryParts'][0]['start'] > 1:
            space = partConf['primaryParts'][0]['start'] - 1
            spaceDict = {
                'start': 1,
                'size': space
            }
            partConf['emptySpaces'].append(spaceDict)

        # check remaining partitions
        for i in range(0, (len(partConf['primaryParts'])-1) ):
            space = partConf['primaryParts'][i+1]['start'] - partConf['primaryParts'][i]['end'] - 1
            if space > 0:
                spaceDict = {
                    'start': partConf['primaryParts'][i]['end'] + 1,
                    'size': space
                }
                partConf['emptySpaces'].append(spaceDict)

        # check disk end
        space = partConf['diskSize'] - partConf['primaryParts'][-1]['end'] - 1
        if space > 0:
            spaceDict = {
                'start': partConf['primaryParts'][-1]['end'] + 1,
                'size': space
            }
            partConf['emptySpaces'].append(spaceDict)


    # Do the same for the extended partitions
    for part in partConf['extendedParts']:
        part['emptySpaces'] = []

        # No primary parts: add entire space
        if len(part['childParts']) == 0:
            spaceDict = {
                'start': part['start'] + 1,
                'size': part['size'],
            }
            part['emptySpaces'].append(spaceDict)
        else:
            # check extended partition beginning
            if part['childParts'][0]['start'] > 1:
                space = part['childParts'][0]['start'] - part['start'] - 1
                spaceDict = {
                    'start': part['start'] + 1,
                    'size': space
                }
                part['emptySpaces'].append(spaceDict)

            # check children partitions
            for i in range(0, (len(part['childParts'])-1) ):
                space = part['childParts'][i+1]['start'] - part['childParts'][i]['end'] - 1
                if space > 0:
                    spaceDict = {
                        'start': part['childParts'][i]['end'] + 1,
                        'size': space
                    }
                    part['emptySpaces'].append(spaceDict)

            # check extended partition end
            space = part['end'] - part['childParts'][-1]['end']
            if space > 0:
                spaceDict = {
                    'start': part['childParts'][-1]['end'] + 1,
                    'size': space
                }
                part['emptySpaces'].append(spaceDict)


    # return dictionary
    return partConf
# parseParts()

def run_multipath(command, interval = 0.0, retry = 1.0):
    """
    Runs the passed multipath command. If it returns a non-zero exit status,
    waits for the passed time and tries again until it exits with zero. Before
    returning, sleeps for the passed interval. Returns the output of the
    command.

    This function was writen because it seems that an invocation of the
    multipath command may sometimes fail when it is done before a previous
    invocation has had time enough to take effect on the system.

    @type  command: basestring
    @param command: multipath command to be run

    @type  interval: float
    @param interval: sleep interval in seconds

    @type  retry: float
    @param retry: time to wait before trying again

    @rtype: basestring
    @returns: command output
    """
    # try at most 10 times
    retries = 0

    while True:
        # run the command
        stream = os.popen(command)
        output = stream.read()
        status = stream.close()

        # exit status is zero or last retry: done
        if not status or retries == 10:
            break

        # wait before retrying
        time.sleep(retry)
        retries += 1

    # sleep for the passed interval
    time.sleep(interval)

    # return the output
    return output
# run_multipath()
