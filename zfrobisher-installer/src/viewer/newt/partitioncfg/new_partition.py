#
# IMPORTS
#
import blivet  # For debug only
from partition_util import *
from snack import *
from partitioner import *
from partition import *
from blivet.devicefactory import DEVICE_TYPE_LVM, DEVICE_TYPE_PARTITION

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_NEWPART
from viewer.__data__ import PART_PROMPT_NEWPART

from viewer.__data__ import PART_LABEL_NAME
from viewer.__data__ import PART_LABEL_MNT
from viewer.__data__ import PART_LABEL_LABEL
from viewer.__data__ import PART_LABEL_CAP
from viewer.__data__ import PART_LABEL_TYPE
from viewer.__data__ import PART_LABEL_FS

from viewer.__data__ import PART_FS_XFS
from viewer.__data__ import PART_FS_EXT3
from viewer.__data__ import PART_FS_EXT4
from viewer.__data__ import PART_FS_SWAP

from viewer.__data__ import PART_LABEL_AVAIL
from viewer.__data__ import PART_LABEL_TOTAL

from viewer.__data__ import PART_LABEL_LVM
from viewer.__data__ import PART_LABEL_STD

from viewer.__data__ import PART_BUTTON_OK
from viewer.__data__ import PART_BUTTON_BACK
#
# CODE
#


class NewPartition:
    """
    Represents the disk selelction screen
    """
    def __init__(self, screen, partitioner, partitions, disks, partitionData):
        # 1. Store parameters
        self._screen = screen
        self._disks = disks
        self._partitioner = partitioner
        self._partitions = partitions
        self._part = partitionData

        # 2. Build form components
        # Prompt for configuring required "boot,root and swap" first
        self._partPromptMsg = TextboxReflowed(40,PART_PROMPT_NEWPART.localize())
        # Parameters Grid
        self._parmsGrid = Grid(2, 7)
        #   Partition name
        self._partNameLabel = Label(PART_LABEL_NAME.localize())
        #   We must have at least boot, swap, root, home parts
        self._partName = Entry(20, "%s"%self._part.name)
        #   Partition mount point
        self._partMntLabel = Label(PART_LABEL_MNT.localize())
        self._partMnt = Entry(20, "%s"%self._part.mountpoint)
        #   Partition label
        self._partLabelLabel = Label(PART_LABEL_LABEL.localize())
        self._partLabel = Entry(20, "%s"%self._part.label)
        #   Partition capacity
        self._partCapLabel = Label(PART_LABEL_CAP.localize())
        self._partCap = Entry(20, "%s"%self._part.capacity)
        #   Partition device grid includes:
        #       Partition device type
        self._partDevTypeLabel = Label(PART_LABEL_TYPE.localize())
        self._partDevTypes = Listbox(1, scroll=1, width=10)
        self._partDevTypes.append(PART_LABEL_LVM.localize(),
                                  DEVICE_TYPE_LVM)
        self._partDevTypes.append(PART_LABEL_STD.localize(),
                                  DEVICE_TYPE_PARTITION)
        self._partDevTypes.setCurrent(self._part.devicetype)
        #   Partition file system
        self._partFSLabel = Label(PART_LABEL_FS.localize())
        self._partFS = Listbox(1, scroll=1, width=10)
        self._partFS.append(PART_FS_XFS, PART_FS_XFS)
        self._partFS.append(PART_FS_EXT3, PART_FS_EXT3)
        self._partFS.append(PART_FS_EXT4, PART_FS_EXT4)
        self._partFS.append(PART_FS_SWAP, PART_FS_SWAP)
        self._partFS.setCurrent(self._part.filesystem)

        #   Partition disk size information grid includes:
        self._availSizeGrid = Grid(2, 1)
        self._totalSizeGrid = Grid(2, 1)
        self._availSizeLabel = Label(PART_LABEL_AVAIL.localize())
        self._totalSizeLabel = Label(PART_LABEL_TOTAL.localize())
        sizes = self._partitioner.getDiskSizes(self._disks)
        self._availSize = Textbox(10, 1, sizes["Avail"].humanReadable(), 0, 1)
        self._totalSize = Textbox(10, 1, sizes["Total"].humanReadable(), 0, 1)

        self._availSizeGrid.setField(self._availSizeLabel, 0, 0)
        self._availSizeGrid.setField(self._availSize, 1, 0)
        self._totalSizeGrid.setField(self._totalSizeLabel, 0, 0)
        self._totalSizeGrid.setField(self._totalSize, 1, 0)

        self._parmsGrid.setField(self._partNameLabel, 0, 0, anchorLeft=1)
        self._parmsGrid.setField(self._partName, 1, 0, anchorLeft=1)
        self._parmsGrid.setField(self._partMntLabel, 0, 1, anchorLeft=1)
        self._parmsGrid.setField(self._partMnt, 1, 1, anchorLeft=1)
        self._parmsGrid.setField(self._partLabelLabel, 0, 2, anchorLeft=1)
        self._parmsGrid.setField(self._partLabel, 1, 2, anchorLeft=1)
        self._parmsGrid.setField(self._partCapLabel, 0, 3, anchorLeft=1)
        self._parmsGrid.setField(self._partCap, 1, 3, anchorLeft=1)
        self._parmsGrid.setField(self._partDevTypeLabel, 0, 4, anchorLeft=1)
        self._parmsGrid.setField(self._partDevTypes, 1, 4, anchorLeft=1)
        self._parmsGrid.setField(self._partFSLabel, 0, 5, anchorLeft=1)
        self._parmsGrid.setField(self._partFS, 1, 5, anchorLeft=1)
        self._parmsGrid.setField(self._availSizeGrid, 0, 6,
                                 padding=(0, 2, 0, 0))
        self._parmsGrid.setField(self._totalSizeGrid, 1, 6,
                                 padding=(0, 2, 0, 0))

        #   Buttons
        self._buttonBar = ButtonBar(self._screen,
                                    [(PART_BUTTON_OK.localize(),
                                      PART_BUTTON_OK.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])
        # 3. Build form
        self._form = GridForm(self._screen,
                              PART_TITLE_NEWPART.localize(), 1, 3)
        self._form.add(self._partPromptMsg, 0, 0, (0,0,0,1))
        self._form.add(self._parmsGrid, 0, 1)
        self._form.add(self._buttonBar, 0, 2)

    def run(self):
        self._form.setCurrent(self._partName)
        result = self._form.run()
        self._screen.popWindow()
        # Parse result
        rc = self._buttonBar.buttonPressed(result)

        if rc == PART_BUTTON_OK.localize():
            # Save user input for the back display
            tempPartition = self._partitioner._tempFormData
            #tempPartition.title = self._partName.value()
            tempPartition.name = self._partName.value()
            tempPartition.mountpoint = self._partMnt.value()
            tempPartition.label = self._partLabel.value()
            tempPartition.capacity = strToSize(self._partCap.value())
            tempPartition.devicetype = self._partDevTypes.current()
            tempPartition.filesystem = self._partFS.current()
            tempPartition.device = None
            return tempPartition.devicetype

        else:
            return "back"
