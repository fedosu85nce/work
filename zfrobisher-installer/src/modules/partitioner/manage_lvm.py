#
# IMPORTS
#
from discinfo import get_hierarchy_lvm
from discinfo import get_hierarchy_physical
from zkvmutils import llecho
from zkvmutils import run

from controller.zkvmerror import ZKVMError

import os
import sys
import time


#
# CONSTANTS AND DEFINITIONS
#
CMD_CREATE_LV = 'yes | lvcreate -L %sK --name %s %s'
CMD_CREATE_PV = 'pvcreate -ff --yes %s'
CMD_CREATE_VG = 'vgcreate -s %dk %s %s'
CMD_DEACTIVATE_LV = 'lv=/dev/%s; lvs $lv || exit 0; lvchange -an $lv'
CMD_DEL_LV = 'lvremove -f %s'
CMD_DEL_PV = 'pvremove -f %s'
CMD_DEL_VG = 'vgremove -f %s'
CMD_EXTEND_VG = 'vgextend %s %s'
CMD_REDUCE_VG = 'vgreduce -f %s %s'
CMD_REMOVE_MISSING_VG = 'vgreduce -f --removemissing %s'
CMD_START_LVM = 'vgchange -ay ibmzkvm_vg_root'
CMD_STOP_LVM = 'vgchange -an'
CMD_UMOUNT_LV = 'lv=%s; grep -q $lv /proc/mounts || exit 0; umount $lv'
CMD_USE_LV = 'lvresize -fn -L %dk %s'

#
# ERROR MESSAGES
#
ERROR_CREATE_LV = 'Error: could not create logical volume "%s"'
ERROR_CREATE_PV = 'Error: could not initialize physical volume "%s"'
ERROR_CREATE_VG = 'Error: could not create volume group "%s"'
ERROR_REMOVE_PV = 'Error: could not remove physical volume from volume group "%s"'
ERROR_RESIZE_LV = 'Error: could not set size for logical volume "%s"'


#
# CODE
#
def adjustPVs(vgUseList, hasMultipath):
    """
    Adjust physical volumns according given command list.

    @type  vgUseList: dict
    @param vgUseList: commands and parameters to adjust PVs.

    @type: bool
    @return: True if success, False otherwise
    """
    path = '/dev/%s'
    if hasMultipath:
        path = '/dev/mapper/%s'

    # run over commands and ajust PVs
    for command in vgUseList:

        # first assign all pvs to the vg
        # (those already assigned will fail but that's ok)
        for pv in command['pvs']:
            run(CMD_EXTEND_VG % (command['name'], path % pv))

        # then remove the deleted ones
        for pv in command['deletedPvs']:

            # command to reduve vg failed: abort
            if run(CMD_REDUCE_VG % (command['name'], path % pv)) != 0:
                llecho(ERROR_REMOVE_PV % command['name'])
                return False

    return True
# adjustPVs()

def createLVs(lvCreateList):
    """
    Creates logical volumns according given command list.

    @type  lvCreateList: dict
    @param lvCreateList: commands and parameters to create LVs.

    @type: bool
    @return: True if success, False otherwise
    """
    # run over commands and create LVs
    for command in lvCreateList:

        # create command
        cmd = CMD_CREATE_LV % (command['size'], command['name'], command['vg'])

        # command to create lv failed: abort
        if run(cmd) != 0:
            llecho(ERROR_CREATE_LV % command['name'])
            return False

    return True
# createLVs()

def createPVs(pvCreateList, hasMultipath):
    """
    Creates physical volumns according given command list.

    @type  pvCreateList: dict
    @param pvCreateList: commands and parameters to create PVs.

    @type: bool
    @return: True if success, False otherwise
    """
    path = '/dev/%s'
    if hasMultipath:
        path = '/dev/mapper/%s'

    # run over commands and create PVs
    for command in pvCreateList:

        # command to create pv failed: abort
        if run(CMD_CREATE_PV % path % command['partition']) != 0:
            llecho(ERROR_CREATE_PV % command['partition'])
            return False

    return True
# createPVs()

def createVGs(vgCreateList, hasMultipath):
    """
    Creates volumn groups according given command list.

    @type  vgCreateList: dict
    @param vgCreateList: commands and parameters to create VGs.

    @type: bool
    @return: True if success, False otherwise
    """
    path = '/dev/%s'
    if hasMultipath:
        path = '/dev/mapper/%s'

    # run over commands and create VGs
    for command in vgCreateList:

        # create command
        cmd = CMD_CREATE_VG % (
            command['extentSize'],
            command['name'],
            ' '.join([path % pv for pv in command['pvs']])
        )

        # command to create vg failed: abort
        if run(cmd) != 0:
            llecho(ERROR_CREATE_VG % command['name'])
            return False

    return True
# createVGs()

def delLvmEntities(pvs, vgs, lvs):
    """
    Deletes the specified LVM volume groups and logical volumes

    @type  pvs: list
    @param pvs: physical volumsn to be deleted

    @type  vgs: list
    @param vgs: volume groups to be deleted

    @type  lvs: list
    @param lvs: logical volumes to be deleted

    @rtype: None
    @returns: Nothing
    """
    path = '/dev/'

    # delete logical volumes
    llecho('Removing LVM logical volumes [%s]' % ', '.join(lvs))
    for lv in lvs:
        if run(CMD_UMOUNT_LV % os.path.realpath('/dev/' + lv)) != 0:
            llecho('Error: could not umount the logical volume "%s"' % lv)
            raise ZKVMError('PARTITIONER', 'LVM', 'DELETE_ENTITIES')

        if run(CMD_DEACTIVATE_LV % lv) != 0:
            llecho('Error: could not deactivate the logical volume "%s"' % lv)
            raise ZKVMError('PARTITIONER', 'LVM', 'DELETE_ENTITIES')

        if run(CMD_DEL_LV % lv) != 0:
            llecho('Error: could not remove the logical volume "%s"' % lv)
            raise ZKVMError('PARTITIONER', 'LVM', 'DELETE_ENTITIES')

    # delete volume groups
    llecho('Removing LVM volume groups [%s]' % ', '.join(vgs))
    for vg in vgs:

        # remove missing disks dependencies to generate consistent metadata,
        # otherwise vgdelete may fail
        run (CMD_REMOVE_MISSING_VG % vg)

        if run(CMD_DEL_VG % vg) != 0:
            llecho('Error: could not remove the volume group "%s"' % vg)
            raise ZKVMError('PARTITIONER', 'LVM', 'DELETE_ENTITIES')

    # delete physical volumns
    llecho('Removing LVM physical volumns [%s]' % ', '.join(pvs))
    for pv in pvs:

        if run(CMD_DEL_PV % os.path.realpath(path + pv)) != 0:
            llecho('Error: could not remove the physical volumn "%s"' % pv)
            raise ZKVMError('PARTITIONER', 'LVM', 'DELETE_ENTITIES')
# delLvmEntities()

def getLvmInfo():
    """
    Scans the disks and gets all LVM references of them.

    @rtype: tuple
    @returns: two lists:
        - all volumn groups on the system
        - all logical volumns on the system
    """
    # get physical information about the disks
    physical = get_hierarchy_physical(use_multipath=False)

    # read disks looking for LVM
    lvmDict = get_hierarchy_lvm(physical)

    # returned dictionary has an unexpected format: abort
    if not ('pvs' and 'vgs') in lvmDict.keys():
        return [], []

    # get all information of returned dictionary
    vgList = []
    lvList = []
    for key, item in lvmDict['vgs'].iteritems():

        # append all volumn groups
        vgList.append(item['name'])

        # append all logical volumns associated with this volumn group
        for lv in item['lvs'].keys():
            lvList.append("%s/%s" % (item['name'], lv))

    return vgList, lvList
# getLvmInfo()

def resizeLVs(lvUseList):
    """
    Resizes LVM entities to use them.

    @type  lvUseList: dict
    @param lvUseList: commands and parameters to resize LVs.

    @type: bool
    @return: True if success, False otherwise
    """
    # resize LVM entities
    for command in lvUseList:

        # create command
        cmd = CMD_USE_LV % (
            command['size'],
            '%s/%s' % (command['vg'], command['name'])
        )

        # execute command
        ret = run(cmd)

        # status 3 is when the size has not changed, so it's ok
        if ret != 0 and ret != 3:
            llecho(ERROR_RESIZE_LV % command['name'])
            return False

    return True
# resizeLVs()

def start(tolerant):
    """
    Activates all existing LVM volume groups

    @type  tolerant: bool
    @param tolerant: tolerant mode status

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Activating all existing LVM volume groups')

    # tolerant mode on: LVM with --partial
    if tolerant == True:
        status = run('%s %s' % (CMD_START_LVM, '--partial'))

    # tolerant mode off: start LVM manually
    else:
        status = run(CMD_START_LVM)

    # cannot start volume groups: fail
    if status != 0:
        llecho('Error: cannot activate LVM volume groups')
        sys.exit(1)
# start()

def stop():
    """
    Deactivates all existing LVM volume groups

    @rtype: None
    @returns: nothing
    """
    # report operation
    llecho('Stopping all LVM volume groups')

    # make 10 tries to stop all volume groups
    status = 0

    for i in range(0, 10):

        # run the command to stop volume groups
        status = run(CMD_STOP_LVM)

        # stopped successfully: quit
        if status == 0:
            break

        # wait 1 second before another try
        time.sleep(1)

    # cannot stop volume groups: fail
    if status != 0:
        llecho('Error: cannot deactivate LVM volume groups')
        raise ZKVMError('PARTITIONER', 'LVM', 'DEACTIVATE_VG')
# stop()
