
# !/usr/bin/python

#
# IMPORTS
#
import blivet  # For debug only
import logging  # For debug only
from partition_util import *
from snack import *
from partition import *
from partitioner import *
from blivet.devicefactory import SIZE_POLICY_AUTO
from blivet.devicefactory import SIZE_POLICY_MAX
from msg_box import *

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_VG
from viewer.__data__ import PART_LABEL_VGDESC
from viewer.__data__ import PART_LABEL_POLICY
from viewer.__data__ import PART_LABEL_NEWVG
from viewer.__data__ import PART_LABEL_NAME
from viewer.__data__ import PART_LABEL_TOTAL
from viewer.__data__ import PART_LABEL_FREE
from viewer.__data__ import PART_BUTTON_DEL
from viewer.__data__ import PART_BUTTON_OK
from viewer.__data__ import PART_BUTTON_BACK
from viewer.__data__ import PART_FORM_RESET

from viewer.__data__ import PART_POLICY_AUTO
from viewer.__data__ import PART_POLICY_MAX
from viewer.__data__ import PART_POLICY_FIXED

from viewer.__data__ import PART_TITLE_PARM_ERR
from viewer.__data__ import PART_ERR_VG_EMPTY_NAME
from viewer.__data__ import PART_ERR_VG_EXIST
from viewer.__data__ import PART_ERR_VG_NO_DISK
from viewer.__data__ import PART_ERR_VG_NO_SIZE
# Dummy constant for consistent
SIZE_POLICY_FIXED = 1
#
# CODE
#


class SelectVg:
    """
    Represents the disk selelction screen
    """
    def __init__(self, screen, partitioner, disks, partition):
        # 1. Store parameters
        self._screen = screen
        self._partitioner = partitioner
        self._disks = disks
        self._partition = partition

        # 2. Build form components
        #   VG List
        self._vgInfo = TextboxReflowed(35, PART_LABEL_VGDESC.localize())
        self._vgList = Listbox(1, width=15)
        for vg in self._partitioner.vgs:    # vgs from property of blivet instance
            if self._partitioner.vgInDisks(vg, self._disks):
                self._vgList.append(vg.name, vg)
        self._vgList.append(PART_LABEL_NEWVG.localize(), None)
        if (self._partition is not None) and \
           (self._partition.device is not None) and \
           (type(self._partition.device) == LVMLogicalVolumeDevice):
            self._vgList.setCurrent(self._partition.device.vg)
        else:
            self._vgList.setCurrent(None)

        vg = self._vgList.current()
        self._diskTree = CheckboxTree(5, scroll=1, width=30)
        #   Name grid includes:
        self._nameGrid = Grid(2, 1)
        self._nameLabel = Label(PART_LABEL_NAME.localize())
        self._name = Entry(10, vg.name if vg is not None else "")
        self._nameGrid.setField(self._nameLabel, 0, 0, anchorLeft=1)
        self._nameGrid.setField(self._name, 1, 0, anchorLeft=1)

        #   Disk Tree
        self._diskTree = CheckboxTree(5, scroll=1, width=35)
        freeSpaces = self._partitioner.getFreeSpace(self._disks)
        for disk in self._disks:
            if vg is None:
                self._diskTree.addItem(
                    "%s    %-9s  %.2fMB" %
                    (disk.name, disk.size,
                     (float)(freeSpaces[disk.name][0].convertTo("m"))),
                    (snackArgs['append'], ),
                    disk, 0)
            else:
                if self._partitioner.vgInDisk(vg, disk):
                    self._diskTree.addItem(
                        "%s    %-9s  %.2fMB" %
                        (disk.name, disk.size,
                         (float)(freeSpaces[disk.name][0].convertTo("m"))),
                        (snackArgs['append'], ),
                        disk, 1)
                else:
                    self._diskTree.addItem(
                        "%s    %-9s  %.2fMB" %
                        (disk.name, disk.size,
                         (float)(freeSpaces[disk.name][0].convertTo("m"))),
                        (snackArgs['append'], ),
                        disk, 0)
        #   Info grid includes:
        self._infoGrid = Grid(4, 1)
        self._totalLabel = Label(PART_LABEL_TOTAL.localize())
        self._total = Textbox(10, 1,
                              "%dMB" % vg.size if vg is not None else "",
                              wrap=1)
        self._freeLabel = Label(PART_LABEL_FREE.localize())
        self._free = Textbox(10, 1,
                             "%dMB" % max(0, vg.freeSpace) if vg is not None else "",
                             wrap=1)
        self._infoGrid.setField(self._totalLabel, 0, 0)
        self._infoGrid.setField(self._total, 1, 0)
        self._infoGrid.setField(self._freeLabel, 2, 0)
        self._infoGrid.setField(self._free, 3, 0)

        #   Size grid includes:
        self._sizeGrid = Grid(3, 1)
        self._policyLabel = Label(PART_LABEL_POLICY.localize())
        self._policyList = Listbox(1, scroll=1, width=10)
        self._policyList.append(PART_POLICY_AUTO.localize(), SIZE_POLICY_AUTO)
        self._policyList.append(PART_POLICY_MAX.localize(), SIZE_POLICY_MAX)
        self._policyList.append(PART_POLICY_FIXED.localize(),
                                SIZE_POLICY_FIXED)

        self._size = Entry(10, "")

        if vg is None:
            self._policyList.setCurrent(SIZE_POLICY_AUTO)
        else:
            if vg in self._partitioner.newVgs.keys():
                if self._partitioner.newVgs[vg] > 0:
                    self._policyList.setCurrent(SIZE_POLICY_FIXED)
                    self._size.set(("%d " + SIZE_UNITS_IN_FACTORY) % self._partitioner.newVgs[vg])
                else:
                    self._policyList.setCurrent(self._partitioner.newVgs[vg])
            else:
                self._policyList.setCurrent(SIZE_POLICY_AUTO)
        # Set the states of the size entry
        if (self._policyList.current() == SIZE_POLICY_AUTO) or \
           (self._policyList.current() == SIZE_POLICY_MAX):
            self._size.setFlags(FLAG_DISABLED, FLAGS_SET)
        else:
            self._size.setFlags(FLAG_DISABLED, FLAGS_RESET)
        self._sizeGrid.setField(self._policyLabel, 0, 0)
        self._sizeGrid.setField(self._policyList, 1, 0)
        self._sizeGrid.setField(self._size, 2, 0)

        #   Buttons
        self._buttonBar = ButtonBar(self._screen,
                                    [(PART_BUTTON_DEL.localize(),
                                      PART_BUTTON_DEL.localize()),
                                     (PART_BUTTON_OK.localize(),
                                      PART_BUTTON_OK.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])

        # 3. Build form
        self._form = GridForm(self._screen, PART_TITLE_VG.localize(), 1, 7)
        self._form.add(self._vgInfo, 0, 0, anchorLeft=1)
        self._form.add(self._vgList, 0, 1, anchorLeft=1)
        self._form.add(self._nameGrid, 0, 2, anchorLeft=1)
        self._form.add(self._diskTree, 0, 3, anchorLeft=1)
        self._form.add(self._infoGrid, 0, 4, anchorLeft=1)
        self._form.add(self._sizeGrid, 0, 5, anchorLeft=1,
                       padding=(0, 1, 0, 0))
        self._form.add(self._buttonBar, 0, 6, anchorLeft=1)

    def run(self):
        self._form.setCurrent(self._vgList)
        # Set callback function
        self._vgList.setCallback(self.on_vg_selected)
        self._policyList.setCallback(self.on_policy_selected)
        result = self._form.run()
        self._screen.popWindow()
        # Parse result
        rc = self._buttonBar.buttonPressed(result)
        if rc == PART_BUTTON_OK.localize():
            # Some parameters are not valid, re-enter VG select form
            if not self.validateParms():
                return PART_FORM_RESET.localize()
        return rc

    def on_vg_selected(self):
        vg = self._vgList.current()
        self._name.set("" if vg is None else vg.name)
        # Clear all selections
        for sel in self._diskTree.getSelection():
            self._diskTree.setEntryValue(sel, 0)
        for disk in self._disks:
            if vg is None:
                self._diskTree.setEntryValue(disk, 0)
            # Only the disks which vg belongs to will be marked selected
            elif self._partitioner.vgInDisk(vg, disk):
                self._diskTree.setEntryValue(disk, 1)
            else:
                self._diskTree.setEntryValue(disk, 0)
        # New VG
        if vg is None:
            self._policyList.setCurrent(SIZE_POLICY_AUTO)
            self._size.set("")
        elif vg in self._partitioner.newVgs.keys():
            if self._partitioner.newVgs[vg] > 0:
                self._policyList.setCurrent(SIZE_POLICY_FIXED)
                self._size.set(("%d " + SIZE_UNITS_IN_FACTORY) % self._partitioner.newVgs[vg])
            else:
                self._policyList.setCurrent(self._partitioner.newVgs[vg])
                self._size.set("")
        else:
            self._policyList.setCurrent(SIZE_POLICY_AUTO)
        self._total.setText("%dMB" % vg.size if vg is not None else "     ")
        self._free.setText("%dMB" % max(0, vg.freeSpace) if
                           vg is not None else "     ")

    def on_policy_selected(self):
        vg = self._vgList.current()
        '''
        if vg is not None:
            if vg in self._partitioner.newVgs.keys():
                oldPolicy = self._partitioner.newVgs[vg]
                if oldPolicy > 0:
                    self._policyList.setCurrent(SIZE_POLICY_FIXED)
                    self._size.set("%d"%oldPolicy)
                else:
                    self._policyList.setCurrent(oldPolicy)
                    '''
        policy = self._policyList.current()
        if (policy == SIZE_POLICY_AUTO) or (policy == SIZE_POLICY_MAX):
            self._size.set("")
            self._size.setFlags(FLAG_DISABLED, FLAGS_SET)
        else:
            self._size.setFlags(FLAG_DISABLED, FLAGS_RESET)
            if vg in self._partitioner.newVgs.keys():
                self._size.set(("%d " + SIZE_UNITS_IN_FACTORY) % self._partitioner.newVgs[vg])
            else:
                self._size.set("")

    def validateParms(self):
        name = self._name.value()
        vg = self._vgList.current()
        # For new VG,
        #   1. You must give a valid vg name.
        if vg is None:
            if len(name.strip()) == 0:
                MsgBox(self._screen, PART_TITLE_PARM_ERR.localize(),
                       PART_ERR_VG_EMPTY_NAME.localize())
                return False
        #   2. New vg is alreay exist.
            existVgsNames = []
            for vg in self._partitioner.vgs:
                if self._partitioner.vgInDisks(vg, self._disks):
                    existVgsNames.append(vg.name)
            if name in existVgsNames:
                MsgBox(self._screen, PART_TITLE_PARM_ERR.localize(),
                       PART_ERR_VG_EXIST.localize() % name)
                return False
        # For both new and exist VG,
        #   1. You must select at least one disk
        selDisks = self._diskTree.getSelection()
        if len(selDisks) == 0:
            MsgBox(self._screen, PART_TITLE_PARM_ERR.localize(),
                   PART_ERR_VG_NO_DISK.localize())
            return False
        #   2. You must give a valid size for policy "Fixed"
        policy = self._policyList.current()
        size = self._size.value().strip()
        if policy == SIZE_POLICY_FIXED and strToSize(size) is None:
            MsgBox(self._screen, PART_TITLE_PARM_ERR.localize(),
                   PART_ERR_VG_NO_SIZE.localize())
            return False
        return True

    @property
    def disks(self):
        return self._diskTree.getSelection()

    @property
    def vg(self):
        return self._vgList.current()

    @property
    def name(self):
        return self._name.value()

    @property
    def size(self):
        '''size is assigned to value of map partitioner.newVgs with number type

        '''
        if self._policyList.current() > 0:  # policy value of > 0 is a fixed size request
            return int(strToSize(self._size.value()).convertTo(spec=SIZE_UNITS_IN_FACTORY))
        else:
            return self._policyList.current()
