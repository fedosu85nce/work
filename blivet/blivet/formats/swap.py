# swap.py
# Device format classes for anaconda's storage configuration module.
#
# Copyright (C) 2009  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Dave Lehman <dlehman@redhat.com>
#

from parted import PARTITION_SWAP, fileSystemType
from ..storage_log import log_method_call
from ..errors import *
from ..util import numeric_type
from ..devicelibs import swap
from . import DeviceFormat, register_device_format

import logging
log = logging.getLogger("blivet")


class SwapSpace(DeviceFormat):
    """ Swap space """
    _type = "swap"
    _name = None
    _udevTypes = ["swap"]
    partedFlag = PARTITION_SWAP
    partedSystem = fileSystemType["linux-swap(v1)"]
    _formattable = True                # can be formatted
    _supported = True                  # is supported
    _linuxNative = True                # for clearpart

    #see rhbz#744129 for details
    _maxSize = 128 * 1024

    def __init__(self, *args, **kwargs):
        """ Create a SwapSpace instance.

            Keyword Arguments:

                device -- path to the underlying device
                uuid -- this swap space's uuid
                label -- this swap space's label
                priority -- this swap space's priority
                exists -- indicates whether this is an existing format

        """
        log_method_call(self, *args, **kwargs)
        DeviceFormat.__init__(self, *args, **kwargs)

        self.priority = kwargs.get("priority")
        self.label = kwargs.get("label")

    def __repr__(self):
        s = DeviceFormat.__repr__(self)
        s += ("  priority = %(priority)s  label = %(label)s" %
              {"priority": self.priority, "label": self.label})
        return s

    @property
    def dict(self):
        d = super(SwapSpace, self).dict
        d.update({"priority": self.priority, "label": self.label})
        return d

    @classmethod
    def labeling(cls):
        """Returns True as mkswap can write a label to the swap space."""
        return True

    @classmethod
    def labelFormatOK(cls, label):
        """Returns True since no known restrictions on the label."""
        return True

    label = property(lambda s: s._getLabel(), lambda s,l: s._setLabel(l),
       doc="the label for this swap space")

    def _setPriority(self, priority):
        if priority is None:
            self._priority = None
            return

        if not isinstance(priority, int) or not 0 <= priority <= 32767:
            raise ValueError("swap priority must be an integer between 0 and 32767")

        self._priority = priority

    def _getPriority(self):
        return self._priority

    priority = property(_getPriority, _setPriority,
                        doc="The priority of the swap device")

    def _getOptions(self):
        opts = ""
        if self.priority is not None:
            opts += "pri=%d" % self.priority

        return opts

    def _setOptions(self, opts):
        if not opts:
            self.priority = None
            return

        for option in opts.split(","):
            (opt, equals, arg) = option.partition("=")
            if equals and opt == "pri":
                try:
                    self.priority = int(arg)
                except ValueError:
                    log.info("invalid value for swap priority: %s" % arg)

    options = property(_getOptions, _setOptions,
                       doc="The swap device's fstab options string")

    @property
    def status(self):
        """ Device status. """
        return self.exists and swap.swapstatus(self.device)

    def setup(self, *args, **kwargs):
        """ Open, or set up, a device. """
        log_method_call(self, device=self.device,
                        type=self.type, status=self.status)
        if not self.exists:
            raise SwapSpaceError("format has not been created")

        if self.status:
            return

        DeviceFormat.setup(self, *args, **kwargs)
        swap.swapon(self.device, priority=self.priority)

    def teardown(self, *args, **kwargs):
        """ Close, or tear down, a device. """
        log_method_call(self, device=self.device,
                        type=self.type, status=self.status)
        if not self.exists:
            raise SwapSpaceError("format has not been created")

        if self.status:
            swap.swapoff(self.device)

    def create(self, *args, **kwargs):
        """ Create the device. """
        log_method_call(self, device=self.device,
                        type=self.type, status=self.status)
        force = kwargs.get("force")
        if not force and self.exists:
            raise SwapSpaceError("format already exists")

        if force:
            self.teardown()
        elif self.status:
            raise SwapSpaceError("device exists and is active")

        try:
            DeviceFormat.create(self, *args, **kwargs)
            swap.mkswap(self.device, label=self.label)
        except Exception:
            raise
        else:
            self.exists = True
            self.notifyKernel()

register_device_format(SwapSpace)

