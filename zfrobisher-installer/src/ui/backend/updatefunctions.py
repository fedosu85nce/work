#!/usr/bin/python

#
# IMPORTS
#
import commands
import glob
import os
import re
import shutil
import subprocess

from ui.backend import env as Env
from ui.backend.disk import getAllHardDisks, getPartitions, isBlockDevice, mount, umount
from ui.config import *


#
# CONSTANTS
#
NEW_YABOOT_ENTRY = "\nimage = %(kernel)s\n       label = %(label)s\n       initrd = %(initrd)s\n       root = %(rootdev)s\n        append = \"root=%(rootdev)s ro crashkernel=1024M rd_NO_LUKS rd_NO_MD console=hvc0 KEYTABLE=us quiet SYSFONT=latarcyrheb-sun16 LANG=en_US.utf8 rd_NO_LVM rd_NO_DM selinux=0 rootfsmode=%(fsmode)s\""


#
# CODE
#
def getzKVMdisks():
    """
    Returns all the disk that has 7 partitions

    @rtype: list
    @returns: list of zKVM disks
    """
    result = []

    devices = getAllHardDisks()

    # get disk that has 7 partitions
    for dev in devices:
        parts = getPartitions(dev)

        if len(parts) == 7:
            result.append(dev)

    return result
# getzKVMdisks()

def getCurrentRootPartition(disk):
    """
    Returns the current root partition

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: string
    @returns: current root partition or None
    """
    mountDir = mount("%s2" % disk)
    if mountDir is None:
        return None

    path = os.path.join(mountDir, "etc/yaboot.conf")
    if not os.path.exists(path):
        return None

    fd = open(path)
    content = fd.read()
    fd.close()

    rootPartition = re.findall("root = .*", content)[0].split("=")[1].strip()

    if not umount(mountDir):
        return None

    return rootPartition
# getCurrentRootPartition()

def getNewRootPartition(disk):
    """
    Returns the new root partition

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: string
    @returns: new root partition or None
    """
    currentRoot = getCurrentRootPartition(disk)
    if currentRoot is None:
        return None

    partition = currentRoot[len(currentRoot)-1:]

    if partition == '2':
        newPartition = '3'
    else:
        newPartition = '2'

    return "%s%s" % (disk, newPartition)
# getNewRootPartition()

def updateYabootFile(rootdev):
    """
    Update /etc/yaboot.conf file with the new values

    @type  rootdev: string
    @param rootdev: root device

    @rtype: boolean
    @returns: True if the /etc/yaboot.conf file was successfully updated; 
              False otherwise
    """
    disk = rootdev[:-1]

    mountDir = mount("%s2" % disk)
    if mountDir is None:
        return False

    path = os.path.join(mountDir, "etc/yaboot.conf")

    initrd = glob.glob("/boot/initrd-*")[0]
    kernel = glob.glob("/boot/vmlinuz-*")[0]
    label = "powerkvm-%s" % kernel.split("-", 1)[1]

    fd = open(path)
    content = fd.read()
    fd.close()

    # get root file syste mode
    fsmode = re.findall("rootfsmode=..", content)
    if len(fsmode) > 0:
        fsmode = fsmode[0].split("=")[1]
    else:
        fsmode = "rw"

    newEntry = NEW_YABOOT_ENTRY % {"kernel": kernel, "label": label, 
                                   "initrd": initrd, "rootdev": rootdev, 
                                   "fsmode": fsmode}

    fd = open(path, "a")
    fd.write(newEntry)
    fd.close()

    # set boot-once parameter
    rc = subprocess.call("nvsetenv boot-once \"%s\" &>/dev/null" % label, shell=True)
    if rc == 1:
        return False

    if not umount(mountDir):
        return False

    return True
# updateYabootFile()

def setupzKVMRepo(directory):
    """
    Set zKVM YUM repository in the directory

    @type  directory: string
    @param directory: path to the directory where the YUM repository should be 
                      created

    @rtype: boolean
    @returns: True if the YUM repository was successfully created; 
              False otherwise
    """
    try:
        fd = open(REPO_CONFIG)
        content = fd.read()
        fd.close()

        kernel = glob.glob("/boot/vmlinuz-*")[0]
        version = kernel.split("-", 1)[1]

        repo = os.path.join(directory, 'etc/yum.repos.d/powerkvm.repo')
        fd = open(repo, "w")
        fd.write(content % {'version': version, 'repo-dir': ZKVM_REPO})
        fd.close()

        return True
    except:
        return False

# setupzKVMRepo()

def createWorkDirectory(disk):
    """
    Create work directory to update system
    The work directory is an union between the current root file system and the
    cow partition content

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: tuple
    @returns: (new root partition, path to the work directory)
    """
    if not isBlockDevice(disk):
        return (None, None)

    currentRoot = getCurrentRootPartition(disk)
    if currentRoot is None:
        return (None, None)

    newRootPartition = getNewRootPartition(disk)
    if newRootPartition is None:
        return (None, None)

    filesystem = Env.get('systemupdate.filesystem')
    if filesystem is None:
        filesystem = ""

    cmd = "union_squashfs_cow %s %s %s \"%s\"" % (currentRoot, TARBALL_REPO, ZKVM_REPO, filesystem)
    status, directory = commands.getstatusoutput(". %s && %s" % (ZKVM_FUNCTIONS, cmd))
    if status != 0:
        return (None, None)

    if not os.path.exists(directory):
        return (None, None)

    return (newRootPartition, directory)
# createWorkDirectory()

def updateSystem(directory, partition):
    """
    Update packages in the system in directory

    @type  directory: string
    @param directory: path to the directory which contains a copy of the whole system

    @type  partition: string
    @param partition: new root device

    @rtype: boolean
    @returns: True if the system was successfully updated;
              False otherwise
    """
    kernel = glob.glob("/boot/vmlinuz-*")[0]
    version = kernel.split("-", 1)[1]

    cmd = "python %s %s %s" % (UPDATE_PKGS_SCRIPT, directory, version)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        return False

    cleanupSystem(directory)

    mountDir = mount(partition)
    if mountDir is None:
        return False

    newrootfs = os.path.join(mountDir, NEW_ROOTFS_IMG)
    if os.path.exists(newrootfs):
        os.remove(newrootfs)

    cmd = "mksquashfs %s %s" % (directory, newrootfs)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        return False

    shutil.rmtree(directory)

    path = os.path.dirname(directory)
    if not umount(path):
        return False

    if not umount(mountDir):
        return False

    return True
# updateSystem()

def cleanupSystem(directory):
    """
    Remove temporary files and directories created during the update process

    @type  directory: string
    @param directory: path to the directory which contains a copy of the whole system

    @rtype: None
    @returns: nothing
    """
    bootDir = os.path.join(directory, 'boot/')
    shutil.rmtree(bootDir, ignore_errors=True)
    shutil.copytree("/boot", bootDir)

    repoDir = os.path.join(directory, ZKVM_REPO[1:])
    shutil.rmtree(repoDir, ignore_errors=True)

    repoConfig = os.path.join(directory, 'etc/yum.repos.d/powerkvm.repo')
    os.remove(repoConfig)

    urandom = os.path.join(directory, 'dev/urandom')
    os.remove(urandom)
# cleanupSystem()

def cpyRootfsToDisk(partition):
    """
    Copy kernel, initrd and root file system imagens to the disk

    @type  partition: string
    @param partition: new root device

    @rtype: boolean
    @returns: True if the all the files was successfully copied into partition;
              False otherwise
    """
    mountDir = mount(partition)
    if mountDir is None:
        return False

    bootDir = os.path.join(mountDir, "boot")
    if os.path.exists(bootDir):
        shutil.rmtree(bootDir, ignore_errors=True)

    shutil.copytree("/boot", bootDir)
    shutil.copy(ROOTFS_IMG, mountDir)

    if not umount(mountDir):
        return False

    return True
# cpyRootfsToDisk()

def restoreCowPartition(disk):
    """
    Restore cow partition when an error occurred during the update process

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: boolean
    @returns: True if the cow partition content was successfully restored; 
              False otherwise
    """
    currentRoot = getCurrentRootPartition(disk)

    mountDir = mount(currentRoot)
    if mountDir is None:
        return False

    cowDir = mount("%s5" % disk)
    if cowDir is None:
        return False

    path = os.path.join(mountDir, COW_BACKUP)
    cmd = "tar -xzp --numeric-owner -f %s -C %s" % (path, cowDir) 
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        return False

    os.remove(path)

    if (not umount(mountDir)) or (not umount(cowDir)):
        return False

    rc = subprocess.call("nvsetenv boot-once \"\" &>/dev/null", shell=True)
    if rc == 1:
        return False

    return True
# restoreCowPartition()
