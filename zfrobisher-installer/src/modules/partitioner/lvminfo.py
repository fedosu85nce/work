#
# IMPORTS
#
import fs

import os
import re


#
# CONSTANTS AND DEFINITIONS
#
_CMD_LVS = 'lvs -o vg_name,lv_name,lv_size --noheadings --units B --nosuffix --separator : 2> /dev/null'
_CMD_PVS = 'pvs -o vg_name,pv_name --noheadings --separator : 2> /dev/null'
_CMD_PVS_BY_LV = 'lvs -o vg_name,lv_name,devices --noheadings --separator : 2> /dev/null'
_CMD_VGS = 'vgs -o vg_name,vg_size,vg_free,vg_extent_size --noheadings --units B --nosuffix --separator : 2> /dev/null'
_DEVICE = re.compile('/dev/(?P<device>[^\(\)]*)')


#
# CODE
#
def _convertToKB(number):
    """
    Convert the passed from bytes to kilobytes

    @type  number: int
    @param number: number to be converted

    @rtype: float
    @returns: number in megabytes
    """
    return int(number) / 1024
#  _convertToKB()

def _detectLogicalVolumes(hierarchy):
    """
    Detects the existing logical volumes. Updates the passed LVM hierarchy
    dictionary.

    @type  hierarchy: dict
    @param hierarchy: LVM hierarchy dictionary

    @rtype: None
    @returns: nothing
    """
    # get volume groups dictionary
    vgs = hierarchy['vgs']

    # make a query for logical volumes
    stdout = os.popen(_CMD_LVS)
    lines = stdout.read().splitlines()
    stdout.close()

    # parse logical group info lines - vg_name:lv_name,lv_size
    for line in lines:
        parts = line.strip().split(':')

        # invalid line: ignore it
        if len(parts) < 3:
            #print 'ERROR', line
            continue

        # expand the parsed fields
        vgName, lvName, lvSize = parts[0:3]

        # volume group does not exist: ignore
        if vgName not in vgs:
            #print 'ERROR', line
            continue

        # get the device for the logical volume
        device = os.path.join('/dev/mapper', vgName + '-' + lvName)

        # add logical group info to its volume group
        vgs[vgName]['lvs'][lvName] = {
            'end': -1,
            'name': lvName,
            'format': None,
            'free': _convertToKB(fs.getFreeSpace(device, -1)),
            'fs': fs.getFileSystem(device),
            'size': _convertToKB(lvSize),
            'start': -1,
            'type': None,
        }
# _detectLogicalVolumes()

def _detectPhysicalVolumes(hierarchy):
    """
    Detects the physical volumes. Updates the passed LVM hierarchy dictionary.

    @type  hierarchy: dict
    @param hierarchy: LVM hierarchy dictionary

    @rtype: None
    @returns: nothing
    """
    # get volume and physical groups dictionaries
    vgs = hierarchy['vgs']
    pvs = hierarchy['pvs']

    # make a query for physical volumes
    stdout = os.popen(_CMD_PVS)
    lines = stdout.read().splitlines()
    stdout.close()

    # parse physical group info lines - vg_name:pv_name
    for line in lines:
        parts = line.strip().split(':')

        # invalid line: ignore it
        if len(parts) < 2:
            #print 'ERROR', line
            continue

        # expand the parsed fields
        vgName, pvName = parts[0:2]

        # physical volume name is not like /dev/bla: ignore it
        match = _DEVICE.search(pvName)

        if match == None:
            #print 'ERROR', line
            continue

        # add the physical volume to the list as its device name
        pvName = match.groupdict()['device']
        pvs.add(pvName)

        # volume group does not exist: ignore
        if vgName not in vgs:
            #print 'ERROR', line
            continue

        # initialize the list of logical volumes that use this pv
        vgs[vgName]['pvsToLvs'][pvName] = set()
# _detectPhysicalVolumes()

def _detectVolumeGroups(hierarchy):
    """
    Detects the existing volume groups and info about them. Updates the passed
    LVM hierarchy dictionary.

    @type  hierarchy: dict
    @param hierarchy: LVM hierarchy dictionary

    @rtype: None
    @returns: nothing
    """
    # get volume groups dictionary
    vgs = hierarchy['vgs']

    # make a query for volume groups
    stdout = os.popen(_CMD_VGS)
    lines = stdout.read().splitlines()
    stdout.close()

    # parse volume group info lines - name:size:free
    for line in lines:
        parts = line.strip().split(':')

        # invalid line: ignore it
        if len(parts) < 4:
            #print 'ERROR', line
            continue

        # expand the parsed fields
        vgName, vgSize, vgFree, extentSize = parts[0:4]

        # add volume group info to the hierarchy
        vgs[vgName] = {
            'avail_space': _convertToKB(vgFree),
            'name': vgName,
            'free': _convertToKB(vgFree),
            'lvs': {},
            'pvsToLvs': {},
            'size': _convertToKB(vgSize),
            'type': 'lvm',
            'extentSize': _convertToKB(extentSize),
        }
# _detectVolumeGroups()

def _mapPhysicalToLogical(hierarchy):
    """
    Map the physical volumes to the logical ones where they are used. Updates
    the passed LVM hierarchy dictionary.

    @type  hierarchy: dict
    @param hierarchy: LVM hierarchy dictionary

    @rtype: None
    @returns: nothing
    """
    # get volume groups dictionary
    vgs = hierarchy['vgs']

    # make a query for logical volumes
    stdout = os.popen(_CMD_PVS_BY_LV)
    lines = stdout.read().splitlines()
    stdout.close()

    # parse logical group info lines - vg_name:lv_name:pv_name
    for line in lines:
        parts = line.strip().split(':')

        # invalid line: ignore it
        if len(parts) < 3:
            #print 'ERROR', line
            continue

        # expand the parsed fields
        vgName, lvName, pvName = parts[0:3]

        # volume group does not exist in the hierarchy: ignore it
        if vgName not in vgs:
            #print 'ERROR', line
            continue

        # physical volume name is not like /dev/bla: ignore it
        match = _DEVICE.search(pvName)

        if match == None:
            #print 'ERROR', line
            continue

        # physical volume does not exist in the hierarchy: ignore it
        pvName = match.groupdict()['device']

        if pvName not in vgs[vgName]['pvsToLvs']:
            #print 'ERROR', line
            continue

        # add logical group as an user of the physical volume
        vgs[vgName]['pvsToLvs'][pvName].add(lvName)
# _mapPhysicalToLogical()

def getHierarchy():
    """
    Detects and returns the hierarchy of LVM volume groups, their logical
    and physical volumes.

    @rtype: dict
    @returns: LVM hierarchy
    """
    # initialize hierarchy dictionary
    hierarchy = {
        'pvs': set(),
        'vgs': {},
    }

    # detect the volume groups
    _detectVolumeGroups(hierarchy)

    # detect the logical volumes
    _detectLogicalVolumes(hierarchy)

    # detect the physical volumes
    _detectPhysicalVolumes(hierarchy)

    # map the physical volumes to the logical ones that use them
    _mapPhysicalToLogical(hierarchy)

    # return the built hierarchy dictionary
    return hierarchy
# getHierarchy()
