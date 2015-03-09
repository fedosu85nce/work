# !/usr/bin/python

#
# IMPORTS
#
from snack import *

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_METHOD
from viewer.__data__ import PART_LABEL_DISKDESC
from viewer.__data__ import PART_LABEL_PARTITIONING
from viewer.__data__ import PART_BUTTON_AUTO
from viewer.__data__ import PART_BUTTON_MANUAL
from viewer.__data__ import PART_BUTTON_OK
from viewer.__data__ import PART_BUTTON_BACK
DISK_TREE_HEIGHT = 5

#
# CODE
#


class PartitionMethod:
    """
    Represents partition method selelction screen
    """
    def __init__(self, screen, disks, selectedDisks=[]):
        # 1. Store parameters
        self._screen = screen
        self._disks = disks

        # 2. Build form components
        # Disk Tree
        self._diskInfo = Label(PART_LABEL_DISKDESC.localize())
        self._diskTree = CheckboxTree(DISK_TREE_HEIGHT,
                                      scroll=1,
                                      unselectable=1)
        for disk in self._disks:
            if disk.name in [temp.name for temp in selectedDisks]:
                self._diskTree.append("%s:%s" % (disk.name, disk.size),
                                      disk, 1)
        # Paritioning methods
        self._partInfo = Label(PART_LABEL_PARTITIONING.localize())
        # Partitioning methods grid
        self._partOptsGrid = Grid(2, 1)
        self._partAuto = SingleRadioButton(PART_BUTTON_AUTO.localize(),
                                           None, 1)
        self._partManual = SingleRadioButton(PART_BUTTON_MANUAL.localize(),
                                             self._partAuto, 0)
        self._partOptsGrid.setField(self._partAuto, 0, 0)
        self._partOptsGrid.setField(self._partManual, 1, 0)
        # Buttons
        self._buttonBar = ButtonBar(screen,
                                    [(PART_BUTTON_OK.localize(),
                                      PART_BUTTON_OK.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])

        # Build form
        self._form = GridForm(self._screen, PART_TITLE_METHOD.localize(), 1, 5)
        self._form.add(self._diskInfo, 0, 0, anchorLeft=1)
        self._form.add(self._diskTree, 0, 1)
        self._form.add(self._partInfo, 0, 2, anchorLeft=1)
        self._form.add(self._partOptsGrid, 0, 3)
        self._form.add(self._buttonBar, 0, 4)

    def run(self):
        # Focus on disks tree
        self._form.setCurrent(self._diskTree)
        # Run form
        result = self._form.run()
        self._screen.popWindow()

        # Parse result
        rc = self._buttonBar.buttonPressed(result)

        if rc == PART_BUTTON_OK.localize():
            if self._partAuto.selected():
                return (PART_BUTTON_AUTO.localize(),
                        self._diskTree.getSelection())
            else:
                return (PART_BUTTON_MANUAL.localize(),
                        self._diskTree.getSelection())
        else:
            return (PART_BUTTON_BACK.localize(), self._diskTree.getSelection())
