#
# IMPORTS
#
import itertools
import os
import re
import stat
import tempfile
import time


#
# CONSTANTS AND DEFINITIONS
#
_BLKID_FS = re.compile(' TYPE="(?P<fs>.+)"')
_MOUNTS_FILE = '/proc/mounts'


#
# CODE
#
def getFileSystem(device, default = None):
    """
    Returns the file system type at the passed device. If a file system cannot
    be detected, returns the passed default value.

    @type  device: basestring
    @param device: passed device

    @type  default: arbitrary
    @param default: default value

    @rtype: int
    @returns: free space
    """
    # query the device for the file system    
    stdout = os.popen('blkid %s' % device)
    output = stdout.read().strip()
    stdout.close()

    # file system could not be detected: return default
    match = _BLKID_FS.search(output)

    if match == None:
        return default

    # return the detected file system
    return match.groupdict()['fs']
# getFileSystem()

def getFreeSpace(device, default = None):
    """
    Returns the free space in the file system at the passed device. If the
    device cannot be mounted, returns the passed default value.

    @type  device: basestring
    @param device: passed device

    @type  default: arbitrary
    @param default: default value

    @rtype: int
    @returns: free space
    """
    # error mounting the device: return default value
    mountPoint = mount(device)

    if mountPoint == None:
        return default

    # detect the free space
    info = os.statvfs(mountPoint)
    free = info.f_bavail * info.f_frsize

    # umount the logical volume device
    umount(mountPoint, True)

    # return the free space
    return free
# getFreeSpace()

def hasMedia(device, tries = 3, interval = 1.0):
    """
    Returns True whether there is media in the passed CD/DVD device, False
    otherwise

    @type  tries: int
    @param tries: number of tries to be made

    @type  interval: float
    @param interval: interval in seconds between tries

    @rtype: bool
    @returns: True if there is media, False otherwise
    """
    # path does not exist: no media
    if os.path.exists(device) == False:
        return False

    # not a block device: no media
    if stat.S_ISBLK(os.stat(device).st_mode) == False:
        return False

    # initialize counter
    counter = itertools.count(0)

    # detect if there is media
    while counter.next() < tries:

        # open device
        try:
            stream = open(device, 'r')
            stream.close()

        # cannot open device: wait and try again
        except IOError, e:
            time.sleep(interval)
            continue

        # device opened: media
        return True

    # cannot open device: no media
    return False
# hasMedia()

def isMounted(device, mountPoint = None):
    """
    Returns True if the passed device is mounted at the passed mount point. If
    no mount point is passed, returns True if the device is mounted at any mount
    point.

    @type  device: basetring
    @param device: device to be verified

    @type  mountPoint: basetring
    @param mountPoint: mount poit to be verified

    @rtype: basestring or None
    @returns: mount point if mounted, None otherwise
    """
    # mount point passed: remove trailing slashes from it
    if mountPoint != None:
        mountPoint = mountPoint.rstrip('/')

    # read mounts file
    stream = open(_MOUNTS_FILE, 'r')
    lines = stream.readlines()
    stream.close()

    # verify each entry
    for line in lines:

        # invalid entry: ignore
        parts = line.split()

        if len(parts) < 2:
            continue

        # device does not match: skip
        if parts[0] != device:
            continue

        # no mount point passed or mount point matches: return mount point
        if mountPoint == None or parts[1].rstrip('/') == mountPoint:
            return parts[1]

    # return not mounted value
    return None
# isMounted()

def mount(device, mountPoint = None):
    """
    Mounts a device at a mount point. If a mount point is not passed, creates
    a temporary one. On success, returns the mount point that was used. On fail,
    returns None.

    @type  device: basestring
    @param device: device to be mounted

    @type  mountPoint: basestring
    @param mountPoint: mount point to be used

    @rtype: basestring or None
    @returns: mount point, or None on fail
    """
    temp = False

    # no mount point passed: create a temporary directory for it
    if mountPoint == None:
        mountPoint = tempfile.mkdtemp()
        temp = True

    # mount success: just return the used mount point
    status = os.system('mount %s %s &>/dev/null' % (device, mountPoint))

    if status == 0:
        return mountPoint

    # temporary directory was created but mount failed: remove it
    if temp == True:
        os.rmdir(mountPoint)

    return None
# mount()

def mountDvd(device, mountPoint = None, tries = 3, interval = 1.0):
    """
    Mounts a CD/DVD device at a mount point after ensuring that there is media
    in the drive. If a mount point is not passed, creates a temporary one. On
    success, returns the mount point that was used. On fail, returns None.

    @type  device: basestring
    @param device: device to be mounted

    @type  mountPoint: basestring
    @param mountPoint: mount point to be used

    @type  tries: int
    @param tries: number of tries to be made

    @type  interval: float
    @param interval: interval in seconds between tries

    @rtype: basestring or None
    @returns: mount point, or None on fail
    """
    # device already mounted at the passed mount point: done
    if mountPoint != None and isMounted(device, mountPoint) != None:
        return mountPoint

    # no media in drive: fail
    if hasMedia(device, tries, interval) == False:
        return None

    # try to mount media
    return mount(device, mountPoint)
# mountDvd()

def mountNfs(host, path, mountPoint = None):
    """
    Mounts a NFS folder at a mount point. If a mount point is not passed,
    creates a temporary one.

    @type  host: basestring
    @param host: host address where is the path specified

    @type  path: basestring
    @param path: path in the host that will be mounted

    @type mountPoint:  basestring
    @param mountPoint: path in the local machine to mount the nfs folder

    @rtype:   basestring or None
    @returns: mount point or None on fail
    """
    return mount(host + ':' + path, mountPoint)
# mountNfs()

def umount(mountPoint, removeDir = False):
    """
    Umounts the file system mounted at the passed mount point. If L{removeDir}
    is True, also removes the mount point directory.

    @type  mountPoint: basestring
    @param mountPoint: mount point to be used

    @type  removeDir: bool
    @param removeDir: whether or not to remove the mount point directory

    @rtype: bool
    @returns: True on umount success, False otherwise
    """
    # error umounting: finish
    status = os.system('umount %s' % mountPoint)

    if status != 0:
        return False

    # directory removal requested: do it
    if removeDir == True:
        os.system('rm -rf %s' % mountPoint)

    # umount success
    return True
# umount()

def umountDvd(device):
    """
    Umounts the passed DVD device if mounted. If it is mounted more than once,
    umounts all occurrences.

    @type  device: basestring
    @param device: device to be umounted

    @rtype: bool
    @returns: True on success, False otherwise
    """
    # try to umount while mounted
    while isMounted(device) != None:

        # cannot umount: fail
        if umount(device) == False:
            return False

    # umount success
    return True
# umountDvd()

def bind(mountPoint, bindedMountpoint):
    """
    Bind a mountpoint

    @type  mountPoint: basestring
    @param mountPoint: path

    @type  bindedMountpoint: basestring
    @param bindedMountpoint: path

    @rtype:   basestring
    @returns: mountpoint on success, None otherwise
    """
    # mount success: just return the used mount point
    status = os.system('mount --bind %s %s' % (mountPoint, bindedMountpoint))

    if status == 0:
       return mountPoint
# bind()
