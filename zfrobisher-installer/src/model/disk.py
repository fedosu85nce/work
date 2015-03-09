#!/usr/bin/python

#
# IMPORTS
#
import os
import re
import shutil
import stat
import subprocess

from tempfile import mkdtemp


#
# CONSTANTS
#


#
# CODE
#
def getAllHardDisks():
    """
    Get all hard disks found in the system

    @rtype: list
    @returns: list of all the hard disks found in the system
    """
    result = []

    fd = open("/proc/partitions")
    content = fd.readlines()
    fd.close()

    for line in content:
        line = line.strip().split()

        if len(line) >= 4:
            dev = line[3]
            if ('hd' in dev or 'sd' in dev) and len(dev) == 3:
                result.append(dev)

    return result
# getAllHardDisks()

def getUUID(partition):
    """
    Returns the partition UUID

    @type  partition: basestring
    @param partition: partition

    @rtype: basestring
    @returns: uuid
    """
    blkcmd = 'blkid -o value -s UUID %s' % partition
    proc = subprocess.Popen(blkcmd, shell=True, stdout = subprocess.PIPE)
    uuid = proc.communicate()[0]

    return uuid[:-1]
# getUUID()

def getPartitions(disk):
    """
    Returns all partitions in a disk

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: list
    @returns: list of all partitions in a disk
    """
    fd = open("/proc/partitions")
    content = fd.read()
    fd.close()

    return re.findall("%s.+" % disk, content)
# getPartitions()

def isBlockDevice(disk):
    """
    Check if the disk is a block device

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: boolean
    @returns: True if the disk is a block device; False otherwise
    """
    if not os.path.exists(disk):
        return False

    mode = os.stat(disk).st_mode
    return stat.S_ISBLK(mode)
# isBlockDevice()

def mount(partition, mpoint=None):
    """Mount a partition in a temporaty mount point if mpoint is None.
    If mpoint is specified, partition is mounted on it.

    @type  partition: string
    @param partition: partition name to be mounted
    @type  mpoint: string
    @param mpoint: destination mount point (optional)

    @rtype: string
    @returns: None if the parition could not be mounted; or the mount
    point directory where partition was successfully mounted"""

    if mpoint == None:
        mountDir = mkdtemp()
    else:
        mountDir = mpoint

    cmd = "mount %s %s >/dev/null 2>&1" % (partition, mountDir)

    rc = subprocess.call(cmd, shell=True)

    if rc == 1:
        return None

    return mountDir
# mountPartition()

def umount(directory, removeMountPoint=True):
    """
    Umount some mount point directory

    @type  directory: string
    @param directory: mount point to be umounted

    @type  removeMountPoint: bool
    @param removeMountPoint: True to remove the directory used to mount
                             the device. False otherwise.

    @rtype: boolean
    @returns: True if the directory was successfully umounted; False otherwise
    """
    cmd = "umount %s &>/dev/null" % directory
    rc = subprocess.call(cmd, shell=True)

    if rc == 1:
        # kill all processes that are using the directory and try to umount it again
        subprocess.call("fuser -km %s > /dev/null 2>&1" % directory, shell=True)

        rc = subprocess.call(cmd, shell=True)
        if rc == 1:
            return False

    if removeMountPoint:
        shutil.rmtree(directory, ignore_errors=True)

    return True
# umount()

def mountEnvironment(basedir):
    """
    Mount system directories for installing

    @type  basedir: str
    @param basedir: chroot dir

    @rtype: nothing
    @returns: nothing
    """
    # make sure all necessary directories exists
    if not os.path.isdir('%s/proc' % basedir):
        os.makedirs('%s/proc' % basedir)

    if not os.path.isdir('%s/dev' % basedir):
        os.makedirs('%s/dev' % basedir)

    if not os.path.isdir('%s/sys' % basedir):
        os.makedirs('%s/sys' % basedir)

    if not os.path.isdir('%s/run' % basedir):
        os.makedirs('%s/run' % basedir)

    if not os.path.isdir('%s/dev/pts' % basedir):
        os.makedirs('%s/dev/pts' % basedir)

    if not os.path.isdir('%s/dev/shm' % basedir):
        os.makedirs('%s/dev/shm' % basedir)

    if not os.path.isdir('%s/sys/fs/selinux' % basedir):
        os.makedirs('%s/sys/fs/selinux' % basedir)

    subprocess.call('mount -o bind /proc %s/proc' % basedir , shell=True)
    subprocess.call('mount -o bind /dev %s/dev' % basedir , shell=True)
    subprocess.call('mount -o bind /sys %s/sys' % basedir , shell=True)
    subprocess.call('mount -o bind /run %s/run' % basedir , shell=True)
    subprocess.call('mount -t devpts -o gid=5,mode=620 devpts %s/dev/pts' % basedir , shell=True)
    subprocess.call('mount -t tmpfs -o defaults tmpfs %s/dev/shm' % basedir , shell=True)
    subprocess.call('mount -t selinuxfs -o defaults selinuxfs %s/sys/fs/selinux > /dev/null 2>&1' % basedir , shell=True)
# mountEnvironment()

def umountEnvironment(basedir):
    """
    Umount system directories

    @type  basedir: str
    @param basedir: chroot dir

    @rtype: nothing
    @returns: nothing
    """
    subprocess.call('umount %s/sys/fs/selinux > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/dev/shm > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/dev/pts > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/run > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/sys > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/dev > /dev/null 2>&1' % basedir , shell=True)
    subprocess.call('umount %s/proc > /dev/null 2>&1' % basedir , shell=True)
# umountEnvironment()
