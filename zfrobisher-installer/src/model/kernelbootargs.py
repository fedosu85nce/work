#!/usr/bin/env python
import shlex
import blivet
import modules.i18n.i18n
from yum import logging
from yum import logginglevels

class kernelBootArgs(object):
    '''Kernel boot arguments.'''
    def __init__(self):
        self.__args = set()
        self.__args_dict = {}
        self.__logger = logging.getLogger(__name__)
    def _get_cmdline(self, cmdline_file):
        '''Read the arguments from cmdline_file and return the related dict'''
        try:
            with open(cmdline_file, 'r') as fd:
               cmdline = fd.readline()
        except IOError:
            self.__logger.error("Read %s failed!" % cmdline_file)
            raise IOError
        cmdline = cmdline.strip()
        (l, m, r) = cmdline.rpartition("BOOT_IMAGE=")
        if r.count('"') % 2:
            cmdline = l + m +'"' + r
        cmdline = cmdline.replace("\\x20", "_")
        ls = shlex.split(cmdline)
        inst_prefix = "inst."

        for i in ls:
            if i.startswith(inst_prefix):
                i = i[len(inst_prefix):]
            if "=" in i:
                (k, v) = i.split("=", 1)
            else:
                k = i
                v = None
            if self.__args_dict.get(k) and k == "modprobe.blacklist":
                if v:
                    self.__args_dict[k] = self.__args_dict[k] + " " + v
            else:
                self.__args_dict[k] = v

    def set_args(self, cmdline_file, rootDev, bootDev, swapDev, diskSelected):
        '''set up the attributes of kernelArgs according to the cmdline file.'''
        self._get_cmdline(cmdline_file)
        default_lang = 'en_US.UTF-8'
        default_keymap = 'us'
        default_font = 'latarcyrheb-sun16'
        default_elevator = 'deadline'
        default_crash = '512M'
        default_pci = 'on'
        if modules.i18n.i18n.current_locale:
            default_lang = modules.i18n.i18n.current_locale + '.UTF-8'
        self.__args.add("LANG=%s" % default_lang)
        self.__args.add("vconsole.keymap=%s" % default_keymap)
        self.__args.add("vconsole.font=%s" % default_font)
        if not self.is_valid_boot_dev(bootDev):
            logger.error("%s is not a valid boot device" % (bootDev.name))
            raise RuntimeError('Error running installBootloader')
        self.__args = self.__args | bootDev.dracutSetupArgs()
        self.__args = self.__args | rootDev.dracutSetupArgs()
        self.__args.add("root=%s" % rootDev.fstabSpec)
        if swapDev is not None:
            self.__args = self.__args | swapDev.dracutSetupArgs()
        # Add all the rd parameter for the disks selected as well
        for disk in diskSelected:
            if disk.parents == []:
                self.__args = self.__args | disk.dracutSetupArgs()
            else:
                for dev in disk.parents:
                    self.__args = self.__args | dev.dracutSetupArgs()


        for (k, v) in self.__args_dict.items():
            if k == 'elevator':
                default_elevator = v
            elif k == 'crashkernel':
                default_crash = v
            elif k == 'pci':
                default_pci = v
            else:
                continue

        self.__args.add('elevator=%s' % default_elevator)
        self.__args.add('crashkernel=%s' % default_crash)
        self.__args.add('pci=%s' % default_pci)

    def is_valid_boot_dev(self, bootdev):
        logger = logging.getLogger(__name__)
        if bootdev is None:
            logger.debug('bootdev is None')
            return False
        if isinstance(bootdev, blivet.devices.iScsiDiskDevice):
            logger.debug('boot device can not be iScsi device')
            return False
        if bootdev.format.minSize and bootdev.size < bootdev.format.minSize:
            logger.debug('The size of %s must be larger than %d' % (bootdev,
                        bootdev.format.minSize))
            return False
        if bootdev.format.maxSize and bootdev.size > bootdev.format.maxSize:
            logger.debug('The size of %s must be smaller than %d' % (bootdev,
                        bootdev.format.minSize))
            return False
        if bootdev.encrypted:
            logger.debug('boot device should not be encrypted')
            return False
        return True

    def get_args(self):
        return self.__args
