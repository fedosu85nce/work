#
# IMPORTS
#
import blivet  # For debug only
from partition_util import *
from partition import *
from blivet.devicefactory import DEVICE_TYPE_LVM, DEVICE_TYPE_PARTITION
from snack import *
from partitioner import *

#
# CONSTANTS
#

from viewer.__data__ import PART_TITLE_MANUAL

from viewer.__data__ import PART_LABEL_NAME
from viewer.__data__ import PART_LABEL_MNT
from viewer.__data__ import PART_LABEL_LABEL
from viewer.__data__ import PART_LABEL_CAP
from viewer.__data__ import PART_LABEL_TYPE
from viewer.__data__ import PART_LABEL_FS

from viewer.__data__ import PART_LABEL_AVAIL
from viewer.__data__ import PART_LABEL_TOTAL

from viewer.__data__ import PART_LABEL_LVM
from viewer.__data__ import PART_LABEL_STD

from viewer.__data__ import PART_BUTTON_ADD
from viewer.__data__ import PART_BUTTON_DEL
from viewer.__data__ import PART_BUTTON_MODIFY
from viewer.__data__ import PART_BUTTON_DONE
from viewer.__data__ import PART_BUTTON_BACK

#
# CODE
#


class ManualPartition:
    """
    Represents the manual parformtitioning main screen
    """
    def __init__(self, screen, partitioner, partitions, disks):
        # 1. Store parameters
        self._screen = screen
        self._partitioner = partitioner
        self._disks = disks
        self._partitions = partitions

        # 2. Build form components
        # Left grid
        #   Partitions list
        self._leftGrid = Grid(1, 2)
        self._partList = Listbox(7, scroll=0, width=20, border=1)
        if len(self._partitions) > 0:
            # Display new partition's mount point on the left window except
            # 'swap', which is distinguished by its filesystem
            for partition in self._partitions:
                if partition.filesystem == "swap":
                    self._partList.append(partition.filesystem, partition)
                else:
                    self._partList.append(partition.mountpoint, partition)
                if partition.current:
                    self._partList.setCurrent(partition)
            curPartition = self._partList.current()
            curPartition.current = True
            # Update partition with device information
            if curPartition.device is not None:
                self._partitioner.updatePartWithDev(curPartition,
                                                    curPartition.device)
        else:
             curPartition = Partition()
             curPartition.filesystem=""
             curPartition.devicetype=""
        #   Buttons
        self._partBtnsGrid = Grid(3, 1)
        self._partAddBtn = CompactButton(PART_BUTTON_ADD.localize())
        self._partDelBtn = CompactButton(PART_BUTTON_DEL.localize())
        self._partModifyBtn = CompactButton(PART_BUTTON_MODIFY.localize())
        self._partBtnsGrid.setField(self._partAddBtn, 0, 0, anchorLeft=1)
        self._partBtnsGrid.setField(self._partDelBtn, 1, 0, anchorRight=1)
        self._partBtnsGrid.setField(self._partModifyBtn, 2, 0, anchorRight=1)
        self._leftGrid.setField(self._partList, 0, 0, anchorLeft=1)
        self._leftGrid.setField(self._partBtnsGrid, 0, 1, padding=(0, 1, 0, 0))

        # Right grid
        self._rightGrid = Grid(2, 8)
        #   Partition name
        self._partNameLabel = Label(PART_LABEL_NAME.localize())
        #   We must have at least boot, swap, root, home parts
        if curPartition.devicetype == DEVICE_TYPE_PARTITION:
            if curPartition.device is not None:
                self._partName = Textbox(20,1, curPartition.name)
            else:
                self._partName = Textbox(20,1, "")
        else:
            self._partName = Textbox(20,1, curPartition.name)
        #   Partition mount point
        self._partMntLabel = Label(PART_LABEL_MNT.localize())
        self._partMnt = Textbox(20,1, curPartition.mountpoint)
        #   Partition label
        self._partLabelLabel = Label(PART_LABEL_LABEL.localize())
        self._partLabel = Textbox(20,1, curPartition.label)
        #   Partition capacity
        self._partCapLabel = Label(PART_LABEL_CAP.localize())
        if curPartition.capacity:
            self._partCap = Textbox(20,1, "%s" % curPartition.capacity.humanReadable())  # blivet Size
        else:
            self._partCap = Textbox(20,1, "" )  # blivet Size
        #   Partition device grid includes:
        self._partDevGrid = Grid(1, 1)
        #       Partition device type
        self._partDevTypeLabel = Label(PART_LABEL_TYPE.localize())
        if curPartition.devicetype ==  DEVICE_TYPE_LVM:
            curPartition.devType = "LVM"
        elif curPartition.devicetype == DEVICE_TYPE_PARTITION:
            curPartition.devType = "Standard"
        else:
            curPartition.devType = ""
        self._partDevTypes = Textbox(20,1, curPartition.devType)
        #       Partition device information button
        self._partDevGrid.setField(self._partDevTypes, 0, 0, anchorLeft=1)
        #   Partition file system
        self._partFSLabel = Label(PART_LABEL_FS.localize())
        self._partFS = Textbox(20,1, curPartition.filesystem)
        #   Partition disk size nformation grid includes:
        self._availSizeGrid = Grid(2, 1)
        self._totalSizeGrid = Grid(2, 1)
        self._availSizeLabel = Label(PART_LABEL_AVAIL.localize())
        self._totalSizeLabel = Label(PART_LABEL_TOTAL.localize())
        # Display available and total size
        sizes = self._partitioner.getDiskSizes(self._disks)
        self._availSize = Textbox(10, 1, sizes["Avail"].humanReadable(), 0, 1)
        self._totalSize = Textbox(10, 1, sizes["Total"].humanReadable(), 0, 1)

        self._availSizeGrid.setField(self._availSizeLabel, 0, 0)
        self._availSizeGrid.setField(self._availSize, 1, 0)
        self._totalSizeGrid.setField(self._totalSizeLabel, 0, 0)
        self._totalSizeGrid.setField(self._totalSize, 1, 0)

        self._rightGrid.setField(self._partNameLabel, 0, 0, anchorLeft=1)
        self._rightGrid.setField(self._partName, 1, 0, anchorLeft=1)
        self._rightGrid.setField(self._partMntLabel, 0, 1, anchorLeft=1)
        self._rightGrid.setField(self._partMnt, 1, 1, anchorLeft=1)
        self._rightGrid.setField(self._partLabelLabel, 0, 2, anchorLeft=1)
        self._rightGrid.setField(self._partLabel, 1, 2, anchorLeft=1)
        self._rightGrid.setField(self._partCapLabel, 0, 3, anchorLeft=1)
        self._rightGrid.setField(self._partCap, 1, 3, anchorLeft=1)
        self._rightGrid.setField(self._partDevTypeLabel, 0, 4, anchorLeft=1)
        self._rightGrid.setField(self._partDevGrid, 1, 4, anchorLeft=1)
        self._rightGrid.setField(self._partFSLabel, 0, 5, anchorLeft=1)
        self._rightGrid.setField(self._partFS, 1, 5, anchorLeft=1)
        self._rightGrid.setField(self._availSizeGrid, 0, 6,
                                 padding=(0, 2, 0, 0))
        self._rightGrid.setField(self._totalSizeGrid, 1, 6,
                                 padding=(0, 2, 0, 0))

        # Button bar
        self._buttonBar = ButtonBar(screen,
                                    [(PART_BUTTON_DONE.localize(),
                                      PART_BUTTON_DONE.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])
        # Main grid
        self._grid = Grid(2, 1)
        self._grid.setField(self._leftGrid, 0, 0)
        self._grid.setField(self._rightGrid, 1, 0, padding=(2, 0, 0, 0))

        # Some entryies may have disable state
        #self._updateEntriesState()

        # Build form
        self._form = GridForm(self._screen, PART_TITLE_MANUAL.localize(), 1, 2)
        self._form.add(self._grid, 0, 0)
        self._form.add(self._buttonBar, 0, 1, padding=(0, 2, 0, 0))

    def _updateEntriesState(self):
        # Standard Partition's name is not controlled by user.
        if self._partDevTypes.current() == DEVICE_TYPE_PARTITION:
            self._partName.setFlags(FLAG_DISABLED, FLAGS_SET)
            # self._partMnt.setFlags(FLAG_DISABLED, FLAGS_SET)
        else:
            self._partName.setFlags(FLAG_DISABLED, FLAGS_RESET)
            # self._partMnt.setFlags(FLAG_DISABLED, FLAGS_RESET)
        curPartition = None
        for partition in self._partitions:
            if partition.current:
                curPartition = partition
        # Swap partition can't have mount point
        if curPartition.title == "swap":
            self._partMnt.setFlags(FLAG_DISABLED, FLAGS_SET)
        else:
            self._partMnt.setFlags(FLAG_DISABLED, FLAGS_RESET)

    def _storeSettings(self):
        curPartition = None
        for partition in self._partitions:
            if partition.current:
                curPartition = partition
        curPartition.name = self._partName.value()
        curPartition.mountpoint = self._partMnt.value()
        curPartition.label = self._partLabel.value()
        curPartition.capacity = strToSize(self._partCap.value())  # input text to blivet Size
        curPartition.devicetype = self._partDevTypes.current()
        curPartition.filesystem = self._partFS.current()

    def run(self):
        # Focus on disks tree
        self._form.setCurrent(self._partList)
        # Set callback function
        self._partList.setCallback(self.on_part_selected)
        self._partName.setCallback(self.on_name_changed)
        self._partMnt.setCallback(self.on_mnt_changed)
        self._partLabel.setCallback(self.on_label_changed)
        self._partCap.setCallback(self.on_capacity_changed)
        self._partDevTypes.setCallback(self.on_devtype_changed)
        # Run form
        result = self._form.run()
        self._screen.popWindow()

        if result is self._partAddBtn:
            return PART_BUTTON_ADD.localize()
        if result is self._partDelBtn:
            return PART_BUTTON_DEL.localize()
        if result is self._partModifyBtn:
            return PART_BUTTON_MODIFY.localize()
        # Parse result: OK or BACK
        rc = self._buttonBar.buttonPressed(result)
        return rc

    def on_part_selected(self):
        curPartition = self._partList.current()
        # Mark partition as current
        for partition in self._partitions:
            partition.current = False
        curPartition.current = True
        # Store values to current partition
        if hasattr(curPartition, "device") and \
           (curPartition.device is not None):
            self._partitioner.updatePartWithDev(curPartition,
                                                curPartition.device)
        self._partName.setText(curPartition.name)
        self._partMnt.setText(curPartition.mountpoint)
        self._partLabel.setText(curPartition.label)
        self._partCap.setText("%s" % curPartition.capacity)
        self._partDevTypes.setText(curPartition.devType)
        self._partFS.setText(curPartition.filesystem)

    def on_devtype_changed(self):
        devType = self._partDevTypes.current()
        # LVM name is inputted by user
        if devType == DEVICE_TYPE_LVM:
            if self._partList.current().device is not None:
                self._partName.set(self._partList.current().name)
            else:
                self._partName.set("")
        # STD name is not controlled by user
        else:
            if self._partList.current().device is not None:
                self._partName.set(self._partList.current().name)
            else:
                self._partName.set("")
        # Some entries may have disable state
        #self._updateEntriesState()

    def on_name_changed(self):
        # To Do:
        # Validate name value is valid
        # Name must be all alpha
        # Name length must be less than XX?
        pass

    def on_mnt_changed(self):
        # To Do:
        # Validate mountpoint value is valid
        # Mountpoint must be all alpha
        # Mountpoint length must be less than XX?
        pass

    def on_label_changed(self):
        # To Do:
        # Validate label value is valid
        # Label must be all alpha
        # Label length must be less than XX?
        pass

    def on_capacity_changed(self):
        # To Do:
        # Validate capacity value is valid
        # Capacity must be all digits
        # Capacity length must be less than XX?
        pass

    # Properties of compoents
    @property
    def partList(self):
        return self._partList

    @property
    def partDevTypes(self):
        return self._partDevTypes
