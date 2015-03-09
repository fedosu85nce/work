#
# IMPORTS
#
import logging  # For debug only
import blivet
from partition_util import *
from snack import *
from partition import *
from partitioner import *
from partition_method import *
from select_disk import *
from select_vg import *
from manual_partition import *
from msg_box import *
from new_partition import *
from list_actions import *
from blivet.devicefactory import DEVICE_TYPE_LVM, DEVICE_TYPE_PARTITION
import copy

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_DISKERR
from viewer.__data__ import PART_ERROR_NODISK
from viewer.__data__ import PART_TITLE_DELPART_ERR
from viewer.__data__ import PART_TITLE_MANUALPART_ERR
from viewer.__data__ import PART_ERROR_DEL_REQUIRED
from viewer.__data__ import PART_ERROR_NOT_CONFIG
from viewer.__data__ import PART_TITLE_VG_CONSISTENCY_CHECK
from viewer.__data__ import PART_WARN_MSG_VG_CONSISTENCY_CHECK
from viewer.__data__ import WARNING_MSG_MISS_ESSENTIAL_PART
from viewer.__data__ import PART_TITLE_MANUALPART_MISS_ESSENTIAL_PARTS
from viewer.__data__ import PART_FS_EXT4

INDEX_START_PARTITION = 0
INDEX_PARTITION_METHOD = 1
INDEX_AUTOMATIC_PARTITION = 2
INDEX_MANUAL_PARTITION = 3
INDEX_SELECT_DISK = 4
INDEX_SELECT_VG = 5
INDEX_LIST_ACTIONS = 6
INDEX_BACK = -1
INDEX_FORWARD = -2

#
# CODE
#


class PartitionInterface:
    """
    The interface class to do partitioning
    """
    def __init__(self, screen, partitioner):
        # 1. Store parameters
        self._partitioner = partitioner
        self._screen = screen

    def run(self, selectedDisks, index, runOn="LPAR"):
        # Selected disks may be changed from outside
        self._selectedDisks = selectedDisks
        # Partitions information may be resetted from outside
        # Clear the selected disks while starting partitioning
        if index == INDEX_START_PARTITION:
            index = INDEX_PARTITION_METHOD
        while(True):
            if index == INDEX_BACK or index == INDEX_FORWARD:
                break
            # 1. Select the disks used for partitioning
            if index == INDEX_PARTITION_METHOD:
                self._partitioner.reset()
                index = self._selectDisks()
            # Automatical partitioning
            if index == INDEX_AUTOMATIC_PARTITION:
                # ToDo: Call codes from Modules provided by WangTing
                self._partitioner.createDefaultLVMLayout(self._selectedDisks)
                index = INDEX_LIST_ACTIONS
            # Manual partitioning
            if index == INDEX_MANUAL_PARTITION:
                index = self._manualPartition(runOn)
            if index == INDEX_SELECT_DISK:
                index = self._selectDisk()
            if index == INDEX_SELECT_VG:
                index = self._selectVg()
            if index == INDEX_LIST_ACTIONS:
                index = self._listActions()
        return index

    def _confirmDeleteVg(self, lackDisks):
        diskNames=""
        for disk in lackDisks:
            diskNames+="\n%22s"%disk.name
        text = PART_WARN_MSG_VG_CONSISTENCY_CHECK.localize()%diskNames
        title = PART_TITLE_VG_CONSISTENCY_CHECK.localize()
        formatedText = reflow(text,50)[0]
        rc = ButtonChoiceWindow(self._screen,title,formatedText,width=50)
        return rc

    def _selectDisks(self):
        partitionMethod = PartitionMethod(self._screen,
                                          self._partitioner.disks,
                                          self._selectedDisks)
        (result, self._selectedDisks) = partitionMethod.run()
        # Quit Partition
        if result == PART_BUTTON_BACK.localize():
            return INDEX_BACK
        # User must select at least one disk for partitioning
        if len(self._selectedDisks) == 0:
            MsgBox(self._screen, PART_TITLE_DISKERR.localize(),
                   PART_ERROR_NODISK.localize())
            return INDEX_SELECT_DISKS
        # Check is there any VG on the selected disks having dependency on
        # the unchoosed disks, this may cause data unavailable, let user
        # decide
        lackDisks = self._partitioner.vgConsistencyCheck(self._selectedDisks)
        if lackDisks:
            if self._confirmDeleteVg(lackDisks) == "cancel":
                return INDEX_SELECT_DISKS
        self._partitioner.clearDisks(self._selectedDisks)
        # Chosen to do automatical partitioning
        if result == PART_BUTTON_AUTO.localize():
            if len(self._selectedDisks) == 0:
                MsgBox(self._screen, PART_TITLE_DISKERR.localize(),
                       PART_ERROR_NODISK.localize())
                return INDEX_PARTITION_METHOD
            self._partitioner.clearDisks(self._selectedDisks)
            return INDEX_AUTOMATIC_PARTITION
        # Chosen to do manual partitioning
        else:
            return INDEX_MANUAL_PARTITION

    def _setNewPartitionInfo(self, formType):
        if formType == "Add":
            # Make sure boot, root and swap will be configured
            # before other partitions
            essentialMountPoints = ['/boot', '/']
            configuredMountpoints = []
            configuredFileSystems = []
            for part in self._partitioner.partitions:
                if part.mountpoint:
                    configuredMountpoints.append(part.mountpoint)
                if part._filesystem:
                    configuredFileSystems.append(part.filesystem)
            for mpt in essentialMountPoints:
                if mpt not in configuredMountpoints:
                    self._partitioner._tempFormOptType = "Add"
                    essentialPart = self._partitioner.essentialPartitions[mpt]
                    return essentialPart
            if 'swap' not in configuredFileSystems:
                self._partitioner._tempFormOptType = "Add"
                essentialPart = self._partitioner.essentialPartitions['swap']
                return essentialPart
            return self._getEmptyPart()
        if formType == "Modify":
            self._partitioner._tempFormOptType = "Modify"
            return self._partitioner.curPartition
        if formType == "Back":
            return self._partitioner._tempFormData

    def _getEmptyPart(self):
        partition = Partition()
        partition._name = ""
        partition._mountpoint = ""
        partition._label = ""
        partition._capacity = ""
        partition._devicetype = DEVICE_TYPE_LVM
        partition._filesystem = PART_FS_EXT4
        self._partitioner._tempFormOptType = "Add"
        return partition

    def popPartitionCfgForm(self, formType):
        '''Display partition configure form:
           formType:
                   - Add: When 'ADD' button is clicked
                   - Modify: When 'MODIFY' button is clicked
                   - Back: When the 'BACK' button of "selcet vg/ disk" form is
                     clicked
        '''
        partData = self._setNewPartitionInfo(formType)
        newPartition = NewPartition(self._screen,
                                    self._partitioner,
                                    self._partitioner.partitions,
                                    self._selectedDisks,
                                    partData)
        return newPartition.run()

    def _manualPartition(self, runOn="LPAR"):
        '''Entry for manual partitioning

            :runOn VM   - means could not configure three default partition /boot, swap, /(root)
                   LPAR - means run on LPAR
        '''
        manualPartition = ManualPartition(self._screen,
                                          self._partitioner,
                                          self._partitioner.partitions,
                                          self._selectedDisks)
        result = manualPartition.run()
        if result == PART_BUTTON_ADD.localize():
            # Display new form to collect new partition information
            ret = self.popPartitionCfgForm("Add")
            if ret == DEVICE_TYPE_LVM:
                return INDEX_SELECT_VG
            elif ret == DEVICE_TYPE_PARTITION:
                return INDEX_SELECT_DISK
            else:
                return INDEX_MANUAL_PARTITION
        if result == PART_BUTTON_DEL.localize():
            # Delete partition
            # Remove created device if exist
            if self._partitioner.curPartition is not None:
                self._partitioner.deletePartition(
                    self._partitioner.curPartition)
            return INDEX_MANUAL_PARTITION
        if result == PART_BUTTON_MODIFY.localize():
            if len(manualPartition.partList.key2item) == 0:
                return INDEX_MANUAL_PARTITION
            ret = self.popPartitionCfgForm("Modify")
            if ret == DEVICE_TYPE_LVM:
                return INDEX_SELECT_VG
            elif ret == DEVICE_TYPE_PARTITION:
                return INDEX_SELECT_DISK
            else:
                return INDEX_MANUAL_PARTITION
        if result == PART_BUTTON_DONE.localize():
            # if run on local vm for test, do not check whether configure the device
            lackedEssentialParts = self._partitioner.checkEssentialPartitons()
            if lackedEssentialParts:
                msg = WARNING_MSG_MISS_ESSENTIAL_PART.localize()%lackedEssentialParts
                MsgBox(self._screen, PART_TITLE_MANUALPART_MISS_ESSENTIAL_PARTS.localize(), msg)
                return INDEX_MANUAL_PARTITION
            if runOn == "VM":
                return INDEX_LIST_ACTIONS
            # run on LPAR, this check is required
            msg = PART_ERROR_NOT_CONFIG.localize()
            hasError = False
            for partition in self._partitioner.partitions:
                if partition.device is None:
                    msg = msg + "\t\t" + partition.title + "\n"
                    hasError = True
            if hasError:
                MsgBox(self._screen, PART_TITLE_MANUALPART_ERR.localize(), msg)
                return INDEX_MANUAL_PARTITION
            else:
                return INDEX_LIST_ACTIONS
        if result == PART_BUTTON_BACK.localize():
            return INDEX_PARTITION_METHOD

    def _backToUserConfiguredPart(self):
        ret = self.popPartitionCfgForm("Back")
        if ret == DEVICE_TYPE_LVM:
            return INDEX_SELECT_VG
        elif ret == DEVICE_TYPE_PARTITION:
            return INDEX_SELECT_DISK
        else:
            return INDEX_MANUAL_PARTITION

    def _selectDisk(self):
        # Select Disk for device type: Standard Partition
        if self._partitioner._tempFormOptType == "Add":
            partition = self._partitioner._tempFormData
        else:
            partition = self._partitioner.curPartition
        selectDisk = SelectDisk(self._screen, self._partitioner,
                                self._selectedDisks, partition)
        (ret, selectedDisk) = selectDisk.run()
        if ret == PART_BUTTON_OK.localize():
            # Now it is the time to actually update blivet info
            self._partitioner.handleCreateStandardPartition(selectedDisk)
            return INDEX_MANUAL_PARTITION
        if ret == PART_BUTTON_BACK.localize():
            # Back to the temp partition window to re-configure
            return self._backToUserConfiguredPart()

    def _selectVg(self):
        if self._partitioner._tempFormOptType == "Add":
            partition = self._partitioner._tempFormData
        else:
            partition = self._partitioner.curPartition
        selectVg = SelectVg(self._screen, self._partitioner,
                            self._selectedDisks, partition)

        ret = selectVg.run()
        if ret == PART_BUTTON_DEL.localize():
            if selectVg.vg is not None:
                self._partitioner.removeLogicalVolumeGroup(
                    selectVg.vg,
                    self._partitioner.partitions)
            return INDEX_SELECT_VG
        if ret == PART_BUTTON_OK.localize():
            self._partitioner.handleCreateLVPartition(selectVg)
            return INDEX_MANUAL_PARTITION
        if ret == PART_BUTTON_BACK.localize():
            return self._backToUserConfiguredPart()
        if ret == PART_FORM_RESET.localize():
            return INDEX_SELECT_VG

    def _listActions(self):
        # Apply changes
        listActions = ListActions(self._screen, self._partitioner)
        rc = listActions.run()
        if rc == PART_BUTTON_OK.localize():
            return INDEX_FORWARD
        else:
            # Back to manual partition form
            return INDEX_MANUAL_PARTITION

    def _isUniquePartitionName(self, name):
        for partition in self._partioner.partitions:
            if name == partition.name:
                return False
        return True
