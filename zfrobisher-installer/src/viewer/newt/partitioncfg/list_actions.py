
# !/usr/bin/python

#
# IMPORTS
#
import blivet  # For debug only
import logging  # For debug only
from blivet.devices import *
from snack import *
from partition import *
from blivet.deviceaction \
    import ACTION_TYPE_DESTROY, ACTION_TYPE_RESIZE, ACTION_OBJECT_FORMAT
from partitioner import *

#
# CONSTANTS
#
from viewer.__data__ import PART_TITLE_ACTION
from viewer.__data__ import PART_LABEL_ACTIONDESC
from viewer.__data__ import PART_BUTTON_OK
from viewer.__data__ import PART_BUTTON_BACK

#
# CODE
#


class ListActions:
    """
    Represents the disk selelction screen
    """
    def __init__(self, screen, partitioner):
        # 1. Store parameters
        self._screen = screen
        self._partitioner = partitioner

        # 2. Build form components
        self._actionInfo = TextboxReflowed(80,
                                           PART_LABEL_ACTIONDESC.localize())
        # Title
        title = "%s %s %s %s %s" % (" Order".center(5),
                                    "Action".center(14),
                                    "Type".center(22),
                                    "Device Name".center(22),
                                    "Mountpoint".center(10))
        self._actionTitle = Textbox(80, 1, title, wrap=1)

        #   Action List
        self._actionList = Listbox(10, scroll=1, width=80, border=1)
        self._actions = self._partitioner.actions
        seqNo = 0
        for action in self._actions:
            seqNo = seqNo + 1
            mountpoint = ""
            serial = ""
            if action.type in [ACTION_TYPE_DESTROY, ACTION_TYPE_RESIZE]:
                typeString = action.typeDesc.title()
            else:
                typeString = action.typeDesc.title()
                if action.obj == ACTION_OBJECT_FORMAT:
                    mountpoint = getattr(action.device.format,
                                         "mountpoint", "")
                    if mountpoint is None:
                        mountpoint = ""
            if hasattr(action.device, "description"):
                desc = "%s %s" % (action.device.name,
                                  action.device.description)
                serial = action.device.serial
            elif hasattr(action.device, "disk"):
                desc = "%s %s" % (action.device.name,
                                  action.device.disk.description)
                serial = action.device.disk.serial
            else:
                desc = action.device.name
                serial = action.device.serial
            actionType = typeString
            actionObjectType = action.objectTypeString
            actionDesc = desc

            self._actionList.append("%02d   %-*s %-*s %-*s %-*s" %
                                    (seqNo, 14, actionType, 22,
                                     actionObjectType, 22, actionDesc,
                                     10, mountpoint),
                                    action)

        #   Buttons
        self._buttonBar = ButtonBar(self._screen,
                                    [(PART_BUTTON_OK.localize(),
                                      PART_BUTTON_OK.localize()),
                                     (PART_BUTTON_BACK.localize(),
                                      PART_BUTTON_BACK.localize())])

        # 3. Build form
        self._form = GridForm(self._screen, PART_TITLE_ACTION.localize(), 1, 4)
        self._form.add(self._actionInfo, 0, 0, anchorLeft=1)
        self._form.add(self._actionTitle, 0, 1, anchorLeft=1,
                       padding=(0, 1, 0, 0))
        self._form.add(self._actionList, 0, 2, anchorLeft=1)
        self._form.add(self._buttonBar, 0, 3)

    def run(self):
        # self._form.setCurrent(self._buttonBar)
        result = self._form.run()
        self._screen.popWindow()
        # Parse result
        rc = self._buttonBar.buttonPressed(result)
        return rc
