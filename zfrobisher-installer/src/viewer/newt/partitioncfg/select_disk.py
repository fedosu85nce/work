#
# IMPORTS
#
import blivet  # For debug only
from snack import *
from partitioner import *

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_STDDESC
from viewer.__data__ import PART_TITLE_STD
from viewer.__data__ import PART_BUTTON_OK
from viewer.__data__ import PART_BUTTON_BACK

#
# CODE
#


class SelectDisk:
    """
    Represents the disk selelction screen
    """
    def __init__(self, screen, partitioner, disks, partition):
        # 1. Store parameters
        self._screen = screen
        self._disks = disks
        self._partitioner = partitioner
        self._partition = partition

        # 2.1 Remove LVM device if exist
        if self._partition.device is not None:
            if self._partition.device is LVMLogicalVolumeDevice:
                self._partitioner.removeLogicalVolume(self._partition)
            else:
                self._partitioner.removeStandardPartition(self._partition)
        # Remember last disk selection if exist
        if (self._partition.device is not None) and \
           (self._partition.device is PartitionDevice):
            lastDisk = self._partition.device.disk
        # 2. Build form components
        #   Disk Tree
        self._diskInfo = TextboxReflowed(50, PART_TITLE_STDDESC.localize())
        self._diskList = Listbox(5, scroll=1, width=40, border=1)
        for disk in self._disks:
            sizes = self._partitioner.getFreeSpace([disk, ])
            self._diskList.append("%s  %sMB  %.2fMB" % (disk.name, disk.size,
                                  (float)(sizes[disk.name][0].convertTo("m"))),
                                  disk)
            # Restore previous setting
            if (self._partition.device is not None) and \
               (self._partition.device is PartitionDevice):
                self._diskList.setCurrent(lastDisk)
        #   Buttons
        self._buttonBar = ButtonBar(screen,
                                    [(PART_BUTTON_OK.localize(),
                                      PART_BUTTON_OK.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])
        # 3. Build form
        self._form = GridForm(self._screen, PART_TITLE_STD.localize(), 1, 3)
        self._form.add(self._diskInfo, 0, 0)
        self._form.add(self._diskList, 0, 1)
        self._form.add(self._buttonBar, 0, 2)

    def run(self):
        self._form.setCurrent(self._diskList)
        result = self._form.run()
        self._screen.popWindow()
        # Parse result
        rc = self._buttonBar.buttonPressed(result)
        selectedDisk = self._diskList.current()
        return (rc, selectedDisk)
