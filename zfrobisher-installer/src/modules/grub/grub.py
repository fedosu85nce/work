#!/usr/bin/python


#
# IMPORTS
#
import logging


#
# CONSTANTS
#
TTY='console=tty0'
HVC='console=hvc0'
CRASHKERNEL='crashkernel=1024M'
LVDATA='rd.lvm.lv=zkvm_vgdata/data'
LVLOG='rd.lvm.lv=zkvm_vglog/log'
LVROOT='rd.lvm.lv=zkvm/root'
LVSWAP='rd.lvm.lv=zkvm/swap'

class Grub:
    """Handle all grub operations"""

    def __init__(self):
        """
        Constructor

        @rtype: None
        @return: Nothing
        """
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def setDefaultOptions(self, path):
        """
        Set default options in /etc/default/grub

        @rtype: None
        @return: Nothing
        """
        default='%s %s %s %s %s %s %s' % (
            TTY, HVC, CRASHKERNEL, LVDATA, LVLOG, LVROOT, LVSWAP)

        with open(path, 'w') as f:
            f.write("GRUB_CMDLINE_LINUX_DEFAULT=\"%s\"" % default)
            f.write("\nGRUB_DISABLE_SUBMENU=true")
            f.write("\nGRUB_DISABLE_RECOVERY=true")
    # setDefaultOptions()

# Grub
