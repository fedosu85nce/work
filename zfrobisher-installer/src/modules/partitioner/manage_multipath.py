#
# IMPORTS
#
from zkvmutils import run

import os


#
# CONSTANTS AND DEFINITIONS
#
CMD_TURNOFF_MULTIPATH = 'multipath -F'
MPATH_FIND_DM = 'dmsetup info -c --noheadings -o minor /dev/mapper/%s'
SYS_DM_PATH = '/sys/block/dm-%s/slaves/'


#
# CODE
#
def detect_multipath_scheme():
    """
    Detects an return the multipath scheme of the system.

    @rtype: dictionary
    @returns: a dictionary with the multipath masters as key and the values
              are a list of strings of the slaves names.
    """
    # turn on multipath
    run_multipath('multipath -r', 1.0)

    # get the master names
    masters = run_multipath('multipath -l -v1').split()

    # get all its slaves and build topology
    topology = {}

    for master in masters:

        # get device mapper id
        stream = os.popen(MPATH_FIND_DM % master)
        mpathDm = stream.read().strip()
        status = stream.close() or 0

        # no valid device mapper id: skip
        if status != 0:
            continue

        # get slaves of this device mapper
        topology[master] = os.listdir(SYS_DM_PATH % mpathDm)

    # return the topology
    return topology
# detect_multipath_scheme()

def run_multipath(command, interval = 0.0, retry = 1.0):
    """
    Runs the passed multipath command. If it returns a non-zero exit status,
    waits for the passed time and tries again until it exits with zero. Before
    returning, sleeps for the passed interval. Returns the output of the
    command.

    This function was writen because it seems that an invocation of the
    multipath command may sometimes fail when it is done before a previous
    invocation has had time enough to take effect on the system.

    @type  command: basestring
    @param command: multipath command to be run

    @type  interval: float
    @param interval: sleep interval in seconds

    @type  retry: float
    @param retry: time to wait before trying again

    @rtype: basestring
    @returns: command output
    """
    # try at most 10 times
    retries = 0

    while True:
        # run the command
        stream = os.popen(command)
        output = stream.read()
        status = stream.close()

        # exit status is zero or last retry: done
        if not status or retries == 10:
            break

        # wait before retrying
        time.sleep(retry)
        retries += 1

    # sleep for the passed interval
    time.sleep(interval)

    # return the output
    return output
# run_multipath()

def setup(hasMultipath, hasLVM, hasRAID, tolerantMode):
    """
    Performs customized configuration when formating multipath disks.

    When creating LVM or RAID, using a mpath device as part of their
    volume or array, it's necessary to turn multipath off because
    IBMIT does not use multipath for installation

    As result tolerantMode, which is retrieved by
    TK_MANAGE_PARTS_TOLERANT variable and used to create volume
    group able to handle IO Errors, will be set to True if there is
    any mpath partition with LVM. Otherwise, tolerantMode will keep
    untouched.

    @type  hasMultipath: bool
    @param hasMultipath: any partition over a multipath device?

    @type  hasLVM: bool
    @param hasLVM: any LVM?

    @type  hasRAID: bool
    @param hasRAID: any soft RAID?

    @type  tolerantMode: bool
    @param tolerantMode: default value for LVM tolerantMode

    @rtype: bool
    @return: LVM tolerant mode override
    """
    return tolerantMode
# setup()
