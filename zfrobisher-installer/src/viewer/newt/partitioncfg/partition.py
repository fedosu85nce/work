from blivet.devicefactory import DEVICE_TYPE_LVM, DEVICE_TYPE_PARTITION

#
# IMPORTS
#

#
# CONSTANTS
#
from viewer.__data__ import PART_FS_XFS
from viewer.__data__ import PART_FS_EXT3
from viewer.__data__ import PART_FS_EXT4
from viewer.__data__ import PART_FS_SWAP
#
# CODE
#


class Partition:
    def __init__(self):
        self._title = ""
        self._name = ""
        self._mountpoint = ""
        self._label = ""
        self._capacity = None  # type is blivet Size
        self._devicetype = DEVICE_TYPE_LVM
        self._filesystem = PART_FS_EXT4
        self._device = None

    @property
    def title(self):
        return self._title

    @property
    def name(self):
        return self._name

    @property
    def mountpoint(self):
        return self._mountpoint

    @property
    def label(self):
        return self._label

    @property
    def capacity(self):
        return self._capacity

    @property
    def devicetype(self):
        return self._devicetype

    @property
    def filesystem(self):
        return self._filesystem

    @property
    def device(self):
        return self._device
