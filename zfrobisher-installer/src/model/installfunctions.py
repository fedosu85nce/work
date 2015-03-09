#!/usr/bin/python

#
# IMPORTS
#
import fcntl
import glob
import os
import re
import shutil
import subprocess
import yum
import sys
import traceback
import urllib2
import blivet
import modules.i18n.i18n
from kernelbootargs import kernelBootArgs

from yum import logging
from yum import logginglevels

from disk import isBlockDevice, mount, umount, getUUID, mountEnvironment, umountEnvironment
from config import *

from callbacks.downloadcallback import DownloadCallback
from callbacks.installationcallback import InstallationCallback
from callbacks.transactioncallback import TransactionCallback

from distutils.version import LooseVersion

from modules.grub.grub import Grub
from modules.identifysystem.identifysystem import IdentifySystem
from controller.zkvmerror import ZKVMError

from modules.partitioner.zkvmutils import getstatusoutput
from subprocess import Popen, PIPE



#
# CONSTANTS
#
DEFAULT_REPO_PATH = 'file:///media/packages/'
INSTALLER_PATH = 'opt/ibm/zkvm-installer/'
DVD_LABEL = '/dev/disk/by-label/ZKVM_LIVECD'
NFS_LOCAL_REPO = '/var/kop'
ZKVM_GPGKEY = '/etc/pki/rpm-gpg/RPM-GPG-KEY-ibm_powerkvm'
CMD_GET_DASD_BUSID = 'lsdasd |grep %s|awk \'{print $1}\''

VGROOT = 'zkvm'
LVROOT = 'root'
LVBOOT = 'boot'
LVSWAP = 'swap'

#
# CODE
#
def createPartitions(disk):
    """
    Create partitions needed by zKVM in the disk

    @type  disk: string
    @param disk: path to the disk [/dev/<name>]

    @rtype: boolean
    @returns: True if the partitions were created in the disk; False otherwise
    """
    if not isBlockDevice(disk):
        return False

    cmd = "dmesg -n1 && sfdisk %s < %s > /dev/null 2>&1" % (disk, PARTITION_LAYOUT)
    rc = subprocess.call(cmd, shell=True)

    if rc == 0:
        return True

    return False
# createPartitions()


def formatPartition(partition):
    """
    Format partition using ext4

    @type  partition: string
    @param partition: path to the partition [/dev/<name>]

    @rtype: boolean
    @returns: True if the partition was successfully formatted; False otherwise
    """
    if not isBlockDevice(partition):
        return False

    cmd = "mkfs.ext4 -F -m 0 -b 4096 %s > /dev/null 2>&1" % partition
    rc = subprocess.call(cmd, shell=True)

    if rc == 0:
        return True

    return False
# formatPartition()


def formatSwapPartition(partition):
    """
    Format partition as swap device.

    @type  partition: string
    @param partition: path to the partition [/dev/<name>]

    @rtype: boolean
    @returns: True if the partition was successfully formatted; False otherwise
    """
    if not isBlockDevice(partition):
        return False

    cmd = "mkswap %s > /dev/null 2>&1" % partition
    rc = subprocess.call(cmd, shell=True)

    if rc == 0:
        return True

    return False
# formatSwapPartition()


def cpyBootloader(bootloader, partition):
    """
    Copy bootloader into partition

    @type  bootloader: string
    @param bootloader: path to the bootloader

    @type  partition: string
    @param partition: path to the partition [/dev/<name>]

    @rtype: boolean
    @returns: True if the bootloader was successfully copied to partition;
              False otherwise
    """
    if not isBlockDevice(partition):
        return False

    cmd = "dd if=%s of=%s &>/dev/null" % (bootloader, partition)
    rc = subprocess.call(cmd, shell=True)

    if rc == 0:
        return True

    return False
# cpyBootloader()


def upgradeSystem(rootDevice, callback):
    """
    Upgrades an existing system

    @type  rootDevice: str
    @param rootDevice: path to root device

    @type  callback: InstallationProcess method
    @param callback: method to update progress on screen

    @rtype: None
    @return: Nothing
    """
    logger = logging.getLogger(__name__)

    # handle old vg name
    legacyDevName = '/dev/mapper/vg_root-lv_root'

    if isBlockDevice(rootDevice):
        rootDev = rootDevice
    elif isBlockDevice(legacyDevName):
        rootDev = legacyDevName
    else:
        raise RuntimeError('Root partition [%s] is not valid' % rootDev)

    # mount rootvg device
    rootDir = mount(rootDev)

    # get fstab from installed system
    fstabPath = os.path.join(rootDir, "etc/fstab")

    # read fstab contents
    fd = open(fstabPath)
    content = fd.readlines()
    fd.close()

    # find the /boot device in fstab
    comment = re.compile('^\s*#')
    device = re.compile('^\s*UUID=[^\s]+')

    try:
        bootDev = [device.match(dev).group() for dev in content if '/boot' in dev and not comment.match(dev)]

    except:
        logger.error('/boot not found in the format required')
        return False

    # boot device not found: panic
    if len(bootDev) == 0:
        logger.error('No boot device found in fstab: %s', str(content))
        raise RuntimeError('Boot device not found int the system')

    bootDev = '/dev/disk/by-uuid/%s' % bootDev[0].split('=')[1]

    logger.info('Boot device: %s', bootDev)

    # /mntpoint/boot doesn't exists: create it
    if not os.path.exists(os.path.join(rootDir, "boot")):
        os.makedirs(os.path.join(rootDir, "boot"))

    # mount the /boot accordingly
    cmd = "mount %s %s 2>/dev/null" % (bootDev, os.path.join(rootDir, "boot"))
    rc = subprocess.call(cmd, shell=True)

    # impossible to mount boot: cannot upgrade the system
    if rc != 0:
        logger.error('Cannot mount /boot device (%s)' % bootDev)
        return False

    # do the upgrade
    try:
        upgradePackages(rootDir, callback)

    except:
        umount(bootDev)
        umount(rootDev)
        return False

    # update yaboot.conf file
    updateYabootFile(bootDev, rootDev, rootDir)

    # command to restore SELinux configurations
    cmd = "chroot %s restorecon -R /" % rootDir

    # SELinux restoration failed: error
    if subprocess.call(cmd, shell=True) != 0:
        raise RuntimeError('Error restoring SELinux permissions')

    # can't umount boot device: error
    if not umount(bootDev):
        raise RuntimeError('Error umounting %s', bootDev)

    # can't umount root device: error
    if not umount(rootDev):
        raise RuntimeError('Error umounting %s', rootDev)

    return True
# upgradeSystem()


# remove the devices we don't have now
def installSystem(partitioner, bootDev, rootDev, swapDev, callback, diskSelected, hasMultipath):
    """
    Installs a fresh system on given device.

    @type  partitioner: Partitioner
    @param partitioner: Partitioner instance

    @type  bootDev: DiskDevice
    @param bootDev: DiskDevice instance

    @type  rootDev: DiskDevice
    @param rootDev: DiskDevice instance

    @type  swapDev: DiskDevice
    @param swapDev: DiskDevice instance

    @type  callback: InstallationProcess method
    @param callback: method to update progress on screen

    @type  diskSelected: List
    @param diskSelected: List of DiskDevice instances selected by user

    @type  hasMultipath: Boolean
    @param hasMultipath: if the disks selected has Multipath device

    @rtype: None
    @return: Nothing
    """
    try:
        logger = logging.getLogger(__name__)

        # given boot device is not valid: error
        if not isBlockDevice(bootDev.path):
            raise RuntimeError('Boot partition [%s] is not valid' % bootDev.name)

        # given root device is not valid: error
        if not isBlockDevice(rootDev.path):
            raise RuntimeError('Root partition [%s] is not valid' % rootDev.name)

        # given swap device(if exist) is not valid: error
        if swapDev is not None and not isBlockDevice(swapDev.path):
            raise RuntimeError('Swap partition [%s] is not valid' % swapDev.name)

        # --------------------------------------------------------------------------
        # mount operations: it's important keep the order to mount the devices
        # correctly. After operations the devices must be umounted in opposite order
        # --------------------------------------------------------------------------

        # A) mount root partition in a tmp folder to allow to install the system
        rootDir = mount(rootDev.path)

        # root directory was not mounted correctly: error
        if rootDir is None:
            raise RuntimeError('Root partition [%s] was not mounted correctly' % rootDev)

        # create boot directory inside mounted root dir
        bootPath = os.path.join(rootDir, 'boot')
        os.makedirs(bootPath)

        # B) mount given boot partition on boot directory
        cmd = "mount %s %s 2>/dev/null" % (bootDev.path, bootPath)
        rc = subprocess.call(cmd, shell=True)

        # boot partition was not mounted correctly: error
        if rc != 0:
            raise RuntimeError('Boot partition [%s] was not mounted correctly' % bootDev)

        # create log directory inside mounted root dir
        logPath = os.path.join(rootDir, 'var/log')
        os.makedirs(logPath)

        # C) mount given log partition on log directory
        # we don't have log partition, so get rid of this part
        #cmd = "mount %s %s 2>/dev/null" % (logDev, logPath)
        #rc = subprocess.call(cmd, shell=True)

        # log partition was not mounted correctly: error
        #if rc != 0:
        #    raise RuntimeError('Log partition [%s] was not mounted correctly' % logDev)

        # mount system environment
        mountEnvironment(rootDir)

        # -------------------------------
        # Install system and configure it
        # -------------------------------

        # install packages
        installPackages(rootDir, callback)

        # perform after installation adjusts
        adjustAfterSystemInstallation(rootDir)

        # update fstab file
        # use only the device we have, the function itself will be updated in a seperate patch
        updateFstabFile(rootDir, bootDev, rootDev, swapDev, partitioner)

        # update yaboot.conf file
        # FIXME: we will not use Grub on s390, we need to have a new function generating bootloader in
        # a seperate patch
        #installGrub(bootDev, rootDev, rootDir, prepDev)

        # update multipath
        setupMultipath(rootDir, hasMultipath)

        # the zipl bootloader should be generated at the last step of the installation
        installBootloader(diskSelected, rootDir, bootDev, rootDev, swapDev)

        # --------------------------------
        # umount devices in opposite order
        # --------------------------------
        umountEnvironment(rootDir)

        # can't umount log device: error
        # we don't have logdevice mounted, so get rid of this part
        #if not umount(logPath, False):
        #    raise RuntimeError('Error umounting %s', logPath)

        # can't umount boot device: error
        if not umount(bootPath):
            raise RuntimeError('Error umounting %s', bootPath)

        # can't umount root device: error
        if not umount(rootDev.path):
            raise RuntimeError('Error umounting %s', rootDev.path)

        return True
    except ZKVMError:
        logger.critical("Failed installSystem")
        raise
    except Exception as e:
        logger.critical("Failed installSystem")
        logger.critical("EXCEPTION:" + str(type(e)))
        logger.critical(str(e))
        logger.critical("Stacktrace:" + str(traceback.format_exc()))
        raise ZKVMError("INSTALLER", "INSTALLSYSTEM", "INSTALL_MSG")
# installSystem()


def getRepoUrl():
    """
    Get the repo URL from the boot parameter

    @rtype:   str
    @returns: repo from cmdline or None if not found
    """
    # open /proc/cmdline and get its content
    fd = open('/proc/cmdline')
    content = fd.read()
    fd.close()

    # split options in a array
    options = content.split()

    # look for repo= option
    for option in options:

        # not the option: skip
        if not 'repo=' in option:
            continue

        # remove repo= from the param
        repo = option.split('=', 1)[1]

        # check if repo is http/https/ftp/nfs and return
        if re.match('(https?|ftp|nfs)://', repo) is not None:
            return repo

    return None
# getRepoUrl()


def getRepoLocal():
    """
    Get the repo URL from NFS boot

    @rtype:   str
    @returns: repo from cmdline or None if repo not found
    """
    # exclusive directory is found: return it as our repo
    if os.path.isdir(NFS_LOCAL_REPO):
        return "file://%s" % NFS_LOCAL_REPO

    return None
# getRepoLocal()


def getRepoDVD():
    """
    Get the repo from the DVD

    @rtype:   str
    @returns: repo from cmdline or None if repo not found
    """
    # DVD is inserted in drive: return the repo name
    if os.path.islink(DVD_LABEL):
        return DEFAULT_REPO_PATH

    return None
# getRepoDVD()


def getRepo():
    """
    Get the repository to install the system

    @rtype:   str
    @returns: repo from cmdline or None if repo not found
    """
    # repo found in boot param: return it
    repo = getRepoUrl()
    if repo:
        return repo

    # repo found in nfs mount location: return it
    repo = getRepoLocal()
    if repo:
        return repo

    # kvm on z DVD in the drive: return it
    repo = getRepoDVD()
    if repo:
        return repo

    return None
# getRepo()


def checkSHA1(repofile, logger):

    logger.info('CheckSHA1')
    SHA1_LIVECD = '/primary-livecd.sha1'
    SHA1_REPO = '/tmp/primary.sha1'

    f = open(SHA1_LIVECD, 'rb')
    str1 = f.read()
    f.close()

    os.popen('sha1sum  /tmp/%s > %s 2>/dev/null' % (repofile, SHA1_REPO))

    with open(SHA1_REPO, 'rb') as f:
        return f.read().split()[0] == str1.split()[0]
# checkSHA1()


def getRepodataFile(url, logger):

    logger.info('Get repodata_file ')

    try:
        f = urllib2.urlopen(url + '/repodata/').read().splitlines()
    except Exception, e:
        logger.critical(str(e))
        raise ZKVMError("INSTALLER", "INSTALLPACKAGES", "INVALID_REPO")

    #find *-primary.sqlite.bz2
    for l in f:
        m = re.search('-primary.sqlite.bz2', l)
        if m:
            s = l

    #get only the filename
    d = re.split('([\d\w]+-primary.sqlite.bz2)', s)

    repodata_file = url + '/repodata/' + d[1]

    logger.info('Download repodata_file')
    os.popen('wget -P /tmp/ ' + repodata_file + ' 2>/dev/null')

    return d[1]
#getRepodataFile()


def upgradePackages(rootDir, callback):
    """
    Updates all packages of given repository on root directory.

    @type  rootDir: str
    @param rootDir: path to temporary folder mounting root device

    @type  callback: callable
    @param callback: method to update installation progress

    @rtype: None
    @return: Nothing
    """
    logger = logging.getLogger(__name__)

    # finishes possible old transactions in the installed system
    subprocess.call('chroot %s rpm --rebuilddb > /dev/null 2>&1' % rootDir, shell=True)
    subprocess.call('yum-complete-transaction --installroot=%s > /dev/null 2>&1' % rootDir, shell=True)

    # create temporary folder inside root directory
    basecache = os.path.join(rootDir, 'tmp')

    # get repository according user preference
    repo = getRepo()
    netRepo = False

    logger.info('Repo in use: %s' % repo)

    # no repo found: panic
    if repo is None:
        logger.error('No repo found')
        raise RuntimeError('No repository found in the system')

    # repo is different from default: set a flag indicating
    if repo != DEFAULT_REPO_PATH:
        netRepo = True

    # instantiate yum object
    yb = yum.YumBase()

    # disable all repos
    yb.repos.disableRepo('*')

    # configure yum parameters
    yb.conf.installroot = rootDir
    yb.conf.gpgcheck = False
    yb.conf.assumeyes = True
    yb.conf.cache = 0
    yb.conf.basecachedir = basecache

    # configure callback to watch installation progress
    downloadCallback = DownloadCallback(callback)
    yb.repos.setProgressBar(downloadCallback)

    # local repository to install packages: mount it
    if not netRepo:
        cmd = "mount -o loop %s /media 2>/dev/null" % DVD_LABEL

        # can't mount disk: error
        if subprocess.call(cmd, shell=True) == 1:
            raise RuntimeError('Error mounting local package repository')

    # create a temporary rw folder to yum cache
    cmd = "mount -t ramfs -o size=20m ramfs /var/lib/yum 2>/dev/null"

    # can't create yum cache: error
    if subprocess.call(cmd, shell=True) == 1:
        raise RuntimeError('Error creating yum cache')

    # create a temporary repo to point to frobisher packages
    newrepo = yum.yumRepo.YumRepository('frobisher')
    newrepo.name = 'frobisher'
    newrepo.baseurl = [repo]
    newrepo.basecachedir = rootDir
    yb.repos.add(newrepo)
    yb.repos.enableRepo(newrepo.id)
    yb.doRepoSetup(thisrepo=newrepo.id)

    try:
        yb.pkgSack
    except:
        raise RuntimeError('Error creating yum instance')

    ylg = yum.logging.getLogger("yum.verbose.YumBase")
    ylg.setLevel(logging.CRITICAL)

    # mark all packages to install
    yb.repos.populateSack()
    yb.pkgSack.buildIndexes()

    updateObj = yb.up

    # mark packages to update
    logger.debug('Packages to be updated:')
    for i in updateObj.getUpdatesList():
        try:
            yb.update(name=i[0])
            logger.debug('    %s' % i[0])
        except:
            logger.debug('Package %s cannot be update' % i[0])
            pass

    # mark obsoleting packages to update
    logger.debug('Packages obsoleting other packages:')
    for pkg in updateObj.getObsoletesList():
        try:
            yb.update(name=pkg[0])
            logger.debug('    %s' % pkg[0])
        except:
            logger.debug('Package %s cannot be updated' % pkg[0])
            pass

    # install new packages
    installed_pkgs = yb.doPackageLists().installed
    available_pkgs = yb.doPackageLists().available
    new_pkgs = list(set(available_pkgs) - set(installed_pkgs))
    logger.debug('New packages to be installed:')
    for pkg in new_pkgs:
        try:
            yb.install(pkg)
            logger.debug('    %s' % pkg)
        except:
            logger.debug('Package %s cannot be installed' % pkg)
            pass

    # execute
    try:
        yb.resolveDeps()
        yb.buildTransaction()
        yb.processTransaction(
            TransactionCallback(downloadCallback),
            None,
            InstallationCallback(callback))

    # cannot upgrade: re-raise exception
    except Exception, e:
        logger.critical('Error on upgrading: %s' % str(e))
        raise

    ylg.setLevel(logging.DEBUG)

    # close yum instance
    yb.closeRpmDB()
    yb.close()

    # can't umount yum cache: error
    if not umount('/var/lib/yum'):
        raise RuntimeError('Error umounting /var/lib/yum')

    # local repo: umount media
    if not netRepo:

        # can't umount media: error
        if not umount('/media'):
            raise RuntimeError('Error umounting /media')
# upgradePackages()


def installPackages(rootDir, callback):
    """
    Installs all packages of given repository on root directory.

    @type  rootDir: str
    @param rootDir: path to temporary folder mounting root device

    @type  callback: method
    @param callback: method to update installation progress

    @rtype: None
    @return: Nothing
    """
    logger = logging.getLogger(__name__)

    # create temporary folder inside root directory
    basecache = os.path.join(rootDir, 'tmp')
    os.makedirs(basecache)

    # get repository according user preference
    repo = getRepo()
    netRepo = False

    # no repo found: panic

    if repo is None:
        logger.critical('No repository found in the system')
        raise ZKVMError("INSTALLER", "INSTALLPACKAGES", "NO_REPO")

    # repo is different from default: set a flag indicating
    if repo != DEFAULT_REPO_PATH and repo != 'file://' + NFS_LOCAL_REPO:
        netRepo = True
        repodata_file = getRepodataFile(repo, logger)
    # The SHA1 check will fail since the checkSHA1 function needs modification
    # FIXME: Rewrite checkSHA1 or a new function should be here to check SHA1
    #    if not checkSHA1(repodata_file, logger):
    #        raise ZKVMError("INSTALLER", "INSTALLPACKAGES", "INVALID_REPO_CONTENT")

    # fixme: rpm lib writes directly in stdout and breaks the newt screen, we need to
    # import the key before yum tries to use it.
    subprocess.call('rpm --root=%s --initdb' % rootDir, shell=True)
    #zgx:The below code "subprocess..." is commented temporarily for no GPGKEY need.
    #    The check code should be add for whether GPGKEY is needed later.
    #subprocess.call('rpm --root=%s --import %s' % (rootDir, ZKVM_GPGKEY), shell=True)

    # configure yum logger
    yum.logginglevels._added_handlers = True

    yumLogger = yum.logging.getLogger('yum')
    yumLogger.setLevel(logging.DEBUG)
    yumLoggerHandler = yum.logging.FileHandler(filename='/tmp/yum.log', mode='w')
    yumLoggerHandler.setLevel(yum.logging.DEBUG)
    yumLogger.addHandler(yumLoggerHandler)

    # instantiate yum object
    yb = yum.YumBase()

    # disable all repos
    yb.repos.disableRepo('*')

    try:
        yb.pkgSack
    except:
        raise RuntimeError('Error creating yum instance')

    # configure yum parameters
    yb.conf.installroot = rootDir
    yb.conf.assumeyes = True
    yb.conf.cache = 0
    yb.conf.basecachedir = basecache

    # dont check gpg locally
    # FIXME: skip gpg check for now, will need to look into why the pgpcheck will
    # fail on certain packages that will block the installation
    yb.conf.gpgcheck = False
    #if isInternalBuild():
    #    yb.conf.gpgcheck = False


    # local repository to install packages: mount it
    if not netRepo:
        cmd = "mount -o loop %s /media 2>/dev/null" % DVD_LABEL

        # can't mount disk: error
        if subprocess.call(cmd, shell=True) == 1:
            raise RuntimeError('Error mounting local package repository')

    # create a temporary rw folder to yum cache
    cmd = "mount -t ramfs -o size=20m ramfs /var/lib/yum 2>/dev/null"

    # can't create yum cache: error
    if subprocess.call(cmd, shell=True) == 1:
        raise RuntimeError('Error creating yum cache')

    # create a temporary repo to point to frobisher packages
    newrepo = yum.yumRepo.YumRepository('frobisher')

    # dont check gpg locally
    # FIXME: skip the gpgcheck again here, need to come back to see if we need new
    # function for this part
    #if not isInternalBuild():
    #    newrepo.gpgcheck = True
    #    newrepo.gpgkey = 'file://%s' % ZKVM_GPGKEY

    newrepo.name = 'frobisher'
    newrepo.baseurl = [repo]
    newrepo.basecachedir = basecache

    yb.repos.add(newrepo)
    yb.repos.enableRepo(newrepo.id)
    yb.doRepoSetup(thisrepo=newrepo.id)

    # mark all packages to install
    yb.repos.populateSack()
    yb.pkgSack.buildIndexes()
    pkgs = yb.repos.getPackageSack().returnPackages()

    # mark packages to install
    for i in pkgs:

        logger.debug('* Package: %s' % i.name)
        try:
            yb.install(name=i.name)

        except:
            logger.debug("Package %s was not marked to install\n" % i)
            pass

    # configure callback to watch installation progress
    downloadCallback = DownloadCallback(callback, len(pkgs))
    yb.repos.setProgressBar(downloadCallback)
    # execute installation
    try:
        yb.resolveDeps()
        yb.buildTransaction()
        yb.processTransaction(
            TransactionCallback(downloadCallback),
            None,
            InstallationCallback(callback, len(pkgs)))

    except Exception, e:
        logger.critical('Error installing packages: %s' % str(e))
        raise

    # close yum instance
    yb.closeRpmDB()
    yb.close()

    # can't umount yum cache: error
    if not umount('/var/lib/yum'):
        raise RuntimeError('Error umounting /var/lib/yum')

    # local repo: umount media
    if not netRepo:

        # can't umount media: error
        if not umount('/media'):
            raise RuntimeError('Error umounting /media')
# installPackages()


def isInternalBuild():
    """
    Checks whether this running system is an internal build or not

    @rtype: bool
    @returns: True for internal build, False otherwise
    """
    return os.path.isfile('/etc/.dont_verify_gpg')
# isInternalBuild()


def getSelinux():
    # open /proc/cmdline and get its content
    fd = open('/proc/cmdline')
    content = fd.read()
    fd.close()

    # split options in a array
    options = content.split()

    # if nothing selinux=1
    ret = True

    # look for selinux=0 or selinux=1 option
    for option in options:
        if option.lower() == 'selinux=1':
            ret = True

        if option.lower() == 'selinux=0':
            ret = False

    return ret
# getSelinux()


def adjustAfterSystemInstallation(rootDir):
    """
    Executes some routines to configure the fresh installed system properly.

    @type  rootDir: str
    @param rootDir: path to temporary folder mounting root device

    @rtype: None
    @return: Nothing
    """
    logger = logging.getLogger(__name__)

    # finishes possible old transactions in the installed system
    subprocess.call('rm -f %s/var/lib/yum/transaction* > /dev/null 2>&1' % rootDir, shell=True)
    subprocess.call('chroot %s rpm --rebuilddb > /dev/null 2>&1' % rootDir, shell=True)

    # command to update root password on installed system
    cmd = "chroot %s passwd -d root > /dev/null" % rootDir

    # update password failed: error
    if subprocess.call(cmd, shell=True) != 0:
        raise RuntimeError('Error changing root password on installed system')

    # selinux=0 autorelabel on reboot
    if not getSelinux():

        # create a file to relabel after reboot
        cmd = "chroot %s touch /.autorelabel" % rootDir

        # SELinux restoration failed: error
        if subprocess.call(cmd, shell=True) != 0:
            logger.error('Error touching autorelabel: %' % sys.stderr)
            raise RuntimeError('Error restoring SELinux permissions')

        # command to restore SELinux configurations
        cmd = "chroot %s setfiles /etc/selinux/targeted/contexts/files/file_contexts /" % rootDir

        if subprocess.call(cmd, shell=True) != 0:
            logger.error('Error running setfiles: %' % sys.stderr)
            raise RuntimeError('Error restoring SELinux permissions')
# adjustAfterSystemInstallation()


def setupMultipath(rootDir,hasMultipath):
    """
    Setups multipath accordingly and generate initrd

    @type  rootDir: string
    @param rootDir: path to mounted root device

    @type  hasMultipath: boolean
    @param hasMultipath: if diskSelected contains Multipath device

    @rtype: nothing
    @returns: nothing
    """

    # get system directories
    sysdir = os.path.join(rootDir, 'sys')
    procdir = os.path.join(rootDir, 'proc')
    devdir = os.path.join(rootDir, 'dev')
    lvmconf = os.path.join(rootDir, 'etc/lvm/lvm.conf')
    mpathdir = os.path.join(rootDir, 'etc/multipath')

    # if no multipath disk selected, just need to generate initrd
    if not hasMultipath:
        subprocess.call('chroot %s dracut --force > /dev/null 2>&1' % rootDir, shell=True)
        return
    # call multipath commands
    subprocess.call('cp /etc/multipath/* %s' % mpathdir, shell=True)
    subprocess.call(r'sed -i "s@^\(\s*filter =\).*@\1 [ \"r/disk/\", \"r/sd.*/\", \"a/.*/\" ]@" %s' % lvmconf, shell=True)
    subprocess.call('chroot %s mpathconf --enable --with_multipathd y > /dev/null 2>&1' % rootDir, shell=True)
    subprocess.call(r'sed -i "s@add_dracutmodules.*@add_dracutmodules+=\" systemd multipath \"@" %s/lib/dracut/dracut.conf.d/01-dist.conf' % rootDir, shell=True)
    subprocess.call('chroot %s dracut --force > /dev/null 2>&1' % rootDir, shell=True)
# setupMultipath()

def installBootloader(diskSelected, rootDir, bootDev, rootDev, swapDev):
    """
    Install bootloader on selected disk by creating /etc/zipl.conf and issue zipl

    @type  diskSelected:  List
    @param diskSelected:  list of DiskDevices selected by user

    @type  rootDir:  string
    @param rootDir:  root directory that is mounted

    @type  bootDev:  DiskDevice
    @param bootDev:  DiskDevice instance of boot device

    @type  rootDev:  DiskDevice
    @param rootDev:  DiskDevice instance of root device

    @type  swapDev:  DiskDevice
    @param swapDev:  DiskDevice instance of swap device

    @rtype: boolean
    @returns: True if installed, False otherwise
    """

    logger = logging.getLogger(__name__)

    # Set some default values
    default_timeout = 5
    default_label = 'linux'
    default_bootdir = '/boot'

    # get the current kernel version to set the image and initrd
    fin = open('/proc/version')
    line = fin.readline()
    fin.close()

    e = line.strip().split()
    version = e[2]

    kernel = "vmlinuz-%s" % version
    initrd = "initramfs-%s.img" % version

    # set the arguments for the parameter list
    boot_args = kernelBootArgs()
    boot_args.set_args("/proc/cmdline", rootDev, bootDev, swapDev, diskSelected)
    args = boot_args.get_args()

    parms = " ".join(args)

    # set the contents of zipl.conf, including header and image info
    header = ("[defaultboot]\n"
              "defaultauto\n"
              "prompt=1\n"
              "timeout=%(timeout)d\n"
              "default=%(default)s\n"
              "target=/boot\n"
              % {"timeout": default_timeout,
                 "default": default_label})

    stanza = ("[%(label)s]\n"
              "\timage=%(boot_dir)s/%(kernel)s\n"
              "\tramdisk=%(boot_dir)s/%(initrd)s\n"
              "\tparameters=\"%(parms)s\"\n"
              % {"label": default_label,
                 "kernel":kernel,
                 "boot_dir":default_bootdir,
                 "initrd":initrd,
                 "parms":parms})

    # get zipl.conf
    config_file = "etc/zipl.conf"
    config_path = os.path.join(rootDir, config_file)
    config = open(config_path, "w")

    # generate zipl.conf

    config.write(header)
    config.write(stanza)
    config.close()

    # run zipl to install zipl logic
    cmd = 'chroot %s zipl' % (rootDir)
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    logger.debug('Zipl output is: %s', out)
    logger.debug('Zipl error output is: %s', err)
    if proc.returncode != 0:
       logger.error('Error running zipl')
       raise RuntimeError('Error running zipl')
    for line in out.splitlines():
        if line.startswith("Preparing boot device: "):
                # Output here may look like:
                #     Preparing boot device: dasdb (0200).
                #     Preparing boot device: dasdl.
                # We want to extract the device name and pass that.
            name = re.sub(r".+?: ", "", line)
            bootDevName = re.sub(r"(\s\(.+\))?\.$", "", name)
            logger.debug('Zipl bootName is: %s', bootDevName)

    if not bootDevName:
        raise RuntimeError("could not find IPL device")

    # run chreipl to change the boot order to the installed disk
    cmd = 'chroot %s chreipl %s' % (rootDir, '/dev/'+bootDevName)
    if subprocess.call(cmd, shell=True) != 0:
        logger.error('Error running chreipl')
        raise RuntimeError('Error running chreipl')

    return True

# installBootloader()

def installGrub(bootDev, rootDev, rootDir, prepDev):
    """
    Install grub in the installed system

    @type  bootDev: string
    @param bootDev: path to boot device

    @type  rootDev: string
    @param rootDev: path to root device

    @rtype: boolean
    @returns: True if installed, False otherwise
    """
    if not isBlockDevice(bootDev) or not isBlockDevice(rootDev):
        return False

    # get system directories
    etcDir = os.path.join(rootDir, 'etc/')
    sysdir = os.path.join(rootDir, 'sys')
    procdir = os.path.join(rootDir, 'proc')
    devdir = os.path.join(rootDir, 'dev')

    # grub directory
    grubDir = os.path.join(rootDir, 'boot/grub2')

    # set /etc/default/grub
    etcDefault = rootDir + "/etc/default"
    etcDefaultGrub = etcDefault + "/grub"
    if not os.path.isdir(etcDefault):
        os.makedirs(etcDefault)
    grub = Grub()
    grub.setDefaultOptions(etcDefaultGrub)

    # generate grub.cfg
    cmd = 'chroot %s grub2-mkconfig -o /boot/grub2/grub.cfg > /dev/null 2>&1' % rootDir
    if subprocess.call(cmd, shell=True) != 0:
        return False

    # create link in /etc
    if os.path.exists(os.path.join(etcDir, "grub2.cfg")):
        os.remove(os.path.join(etcDir, "grub2.cfg"))

    cmd = 'ln -s /boot/grub2/grub.cfg %s' % os.path.join(etcDir, 'grub2.cfg')
    subprocess.call(cmd, shell=True)

    # clear prep partition
    cmd = 'dd if=/dev/zero of=%s > /dev/null 2>&1' % prepDev
    subprocess.call(cmd, shell=True)

    # install grub2
    cmd = 'chroot %s grub2-install --no-nvram --no-floppy %s > /dev/null 2>&1' % (rootDir, prepDev)
    if subprocess.call(cmd, shell=True) != 0:
        return False

    return True
# installGrub()


def updateYabootFile(bootDev, rootDev, rootDir):
    """
    Update /etc/yaboot.conf file with the new values

    @type  bootDev: string
    @param bootDev: path to boot device

    @type  rootDev: string
    @param rootDev: path to root device

    @rtype: boolean
    @returns: True if the /etc/yaboot.conf file was successfully updated;
              False otherwise
    """
    if not isBlockDevice(bootDev) or not isBlockDevice(rootDev):
        return False

    # get etc directory from installed system
    etcDir = os.path.join(rootDir, 'etc/')

    # etc dir not created yet: do it
    if not os.path.exists(etcDir):
        os.makedirs(etcDir)

    cmd = 'rm -f %s > /dev/null 2>&1' % os.path.join(etcDir, 'yaboot.conf')
    subprocess.call(cmd, shell=True)

    # copy yaboot.conf file to installed system
    shutil.copy(DEFAULT_YABOOT_CONF, etcDir)

    # read yaboot.conf file content from installed system to adjust it
    fd = open(os.path.join(etcDir, 'yaboot.conf'))
    content = fd.read()
    fd.close()

    # replace root device entry
    oldrootdev = re.findall("root=/dev/ram", content)[0].split("=")[1].strip()
    content = re.sub("root=%s" % oldrootdev, "root=%s" % rootDev, content)

    # add firstboot option
    content = re.sub("append = \"", "append = \"firstboot=yes ", content)

    # boot directory
    bootDir = os.path.join(rootDir, 'boot/')

    initrd = glob.glob(bootDir + "initramfs-*.ppc64.img")
    kernel = glob.glob(bootDir + "vmlinuz-*")

    # find the most recent kernel/initrd images
    initrd = str(max([LooseVersion(a) for a in initrd]))
    kernel = str(max([LooseVersion(a) for a in kernel]))

    initrd = initrd.split('/')[-1]
    kernel = kernel.split('/')[-1]

    content = re.sub("/boot/vmlinuz", kernel, content)
    content = re.sub("/boot/initrd.img", initrd, content)

    # create a 'etc' dir inside boot folder to store yaboot.conf file
    if not os.path.exists(os.path.join(bootDir, "etc/")):
        os.makedirs(os.path.join(bootDir, "etc/"))

    # new yaboot.conf file
    newYabootFile = os.path.join(bootDir, "etc/yaboot.conf")
    fd = open(newYabootFile, "w")
    fd.write(content)
    fd.close()

    # create a link in /etc/yaboot.conf
    if os.path.exists(os.path.join(etcDir, "yaboot.conf")):
        os.remove(os.path.join(etcDir, "yaboot.conf"))

    cmd = 'ln -s /boot/etc/yaboot.conf %s' % os.path.join(etcDir, 'yaboot.conf')
    subprocess.call(cmd, shell=True)

    # configure system to update yaboot.conf after upgrade
    kernelconf = os.path.join(etcDir, "sysconfig/kernel")
    if os.path.exists(kernelconf):
        os.remove(kernelconf)

    fd = open(kernelconf, 'w')
    fd.write('UPDATEDEFAULT=yes\n')
    fd.write('DEFAULTKERNEL=kernel\n')
    fd.close()
# updateYabootFile()

# Only need to save the information on the three lvs into fstab
def updateFstabFile(rootDir, bootDev, rootDev, swapDev, partitioner):
    """
    Update /etc/fstab file with the correct information about fresh installed
    system.

    @rtype: None
    @returns: Nothing
    """
    # get etc directory
    etcDir = os.path.join(rootDir, 'etc/')

    # etc dir not created yet: do it
    if not os.path.exists(etcDir):
        os.makedirs(etcDir)

    # copy fstab from live session to use it as reference
    shutil.copy("/etc/fstab", etcDir)

    # get fstab from installed system
    fstabPath = os.path.join(rootDir, "etc/fstab")

    # read fstab contents
    fd = open(fstabPath)
    content = fd.readlines()
    fd.close()

    content.append("#Created by zKVM\n")
    content.append("%s    /        %s    defaults    1 1\n"
                    % (rootDev.fstabSpec, rootDev.format.type))
    content.append("%s    /boot    %s    defaults    1 2\n"
                    % (bootDev.fstabSpec, bootDev.format.type))
    if swapDev is not None:
        content.append("%s    swap     %s    defaults    0 0\n"
                        % (swapDev.fstabSpec, swapDev.format.type))
    # add the devices created by user other than boot, root, swap
    if len(partitioner.partitions) > 3:
        for part in partitioner.partitions:
            if part.title in ["boot","root","swap"]:
                continue
            content.append("%s    %s    %s    defaults    0 0 \n"
                           % (part.device.fstabSpec,
                              part.mountpoint,
                              part.device.format.type))

    # update fstab file with new information
    fd = open(fstabPath, "w")
    fd.writelines(content)
    fd.close()
# updateFstabFile()
