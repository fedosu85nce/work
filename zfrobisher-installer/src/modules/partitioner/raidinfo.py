#
# IMPORTS
#
import fs

import glob
import os
import re


#
# CONSTANTS AND DEFINITIONS
#
_CMD_AUTO_DETECT = 'mdadm --assemble --scan 2> /dev/null'
_CMD_DETAIL = 'mdadm --detail %s -b -v'
_DETAILS = re.compile(r' level=(?P<level>\w+) .*? (spares=(?P<spares>\d+))? .* devices=(?P<devices>.+)')
_CMD_ALL = 'mdadm --detail %s'
_DETAIL_TOTAL = re.compile(r'Array Size : (?P<size>[0-9]+) ')
_LEVEL_TO_INTERNAL = {
    'raid0' : 0,
    '0' : 0,
    'stripe' : 0,
    'raid1' : 1,
    '1' : 1,
    'mirror' : 1,
    'raid4' : 4,
    '4' : 4,
    'raid5' : 5,
    '5' : 5,
    'raid6' : 6,
    '6' : 6,
    'raid10' : 10,
    '10' : 10,
}

#
# CODE
#

# LAMBDA : removes the '/dev/' from the argument string
short = lambda x : x.replace('/dev/','')

def getHierarchy():
    """
    Detects and returns the hierarchy of RAID. It'll look something like:

        {
            'md0': {
                'name': 'md0',
                'level': 5,
                'devices': ['sda2', 'sdb4', 'sdc7', ...],
                'spares': 2,
                'chunkSize': 1024,
                'fileSystem': 'ext3',
                'size' : 4194304,  # 4 GB in KB
                'free' : 2097152,  # 50% free
            }
            ...
        }

    @rtype: dict
    @returns: RAID hierarchy
    """

    # initialize hierarchy dictionary
    hierarchy = {}

    # make a query to detect all devices
    stdout = os.popen(_CMD_AUTO_DETECT)
    stdout.read()
    stdout.close()

    # check every md device:
    for md in glob.glob('/dev/md*'):

        # make a query to detail this md device
        stdout = os.popen(_CMD_DETAIL % md)
        text = stdout.read()
        status = stdout.close() or 0

        # command failed : not a valid device
        if status != 0:
            continue

        # short name for md (e.g: '/dev/md0' -> 'md0')
        shortMd = short(md)

        # apply the regex to get the device's data
        detailsMatch = _DETAILS.search(text.replace('\n', ' '))

        # no match object : something went wrong when parsing, skip it
        if not detailsMatch:
            continue

        # get data of this md device
        detailsDict = detailsMatch.groupdict()

        # there's no spare device : assign 0 to it
        spares = int(detailsDict.get('spares', 0) or 0)

        # convert level to internal int number
        level = _LEVEL_TO_INTERNAL.get(detailsDict['level'], -1)

        # separate partitions, tray spaces and get only the shortname
        devices = [short(x.strip()) for x in detailsDict['devices'].split(',')]

        # get total size
        stdout = os.popen(_CMD_ALL % md)
        text = stdout.read()
        stdout.close()

        # apply regex to get total size
        totalMatch = _DETAIL_TOTAL.search(text.replace('\n', ' '))

        # no match object : something went wrong when parsing, skip it
        if not totalMatch:
            continue

        # get total size (in KB)
        totalDict = totalMatch.groupdict()
        size = int(totalDict.get('size', 0))

        # arrange data
        mdData = {
            'name' : shortMd,
            'level' : level,
            'devices' : devices,
            'spares' : spares,
            # TODO : not implemented
            'chunkSize' : -1,
            'filesystem' : fs.getFileSystem(md),
            'size' : size,  # in KB
            'free' : fs.getFreeSpace(md, -1) / 1024,  # in KB
        }

        # fill this device data on the hierarchy
        hierarchy[shortMd] = mdData

    # return the built hierarchy dictionary
    return hierarchy
# getHierarchy()

#
# ENTRY POINT
#
if __name__ == "__main__":
    print getHierarchy()
