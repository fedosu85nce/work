#
# IMPORTS
#
from time import strftime
from model.config import LIVECD_PARTITIONER_LOG

import os
import sys


#
# CODE
#
def getstatusoutput(cmd):
    """
    This function emulates the behavior of the function with the same name found
    in the module commands.

    @type  cmd: basestring
    @param cmd: command to be run

    @rtype: (int, basestring)
    @returns: command exit status and output
    """
    # run the command
    stream = os.popen('{ ' + cmd + '; } 2>&1', 'r')
    output = stream.read()
    status = stream.close() or 0

    # return status and output
    return status, output
# getstatusoutput()

def lecho(msg):
    """
    Logs the passed message and sends it to /dev/console

    @type  msg: basestring
    @param msg: message to be logged

    @rtype: None
    @returns: nothing
    """
    date = strftime("%H:%M:%S")
    scriptname = sys.argv[0].split('/')[-1]
    streams = []

    try:
        stream_console = open("/dev/console", "w")
        streams.append(stream_console)
        #log_file = os.environ.get("LECHO_LOG")
        log_file = LIVECD_PARTITIONER_LOG

        if log_file != None:
            stream_log = open(log_file, "a")
            streams.append(stream_log)

        for stream in streams:
            print >> stream, "%s [%s] - %s" % (date, scriptname, msg)
            stream.close()

    except:
        pass
# lecho()

def llecho(msg):
    """
    Logs the passed message but does not send it to /dev/console

    @type  msg: basestring
    @param msg: message to be logged

    @rtype: None
    @returns: nothing
    """
    date = strftime("%H:%M:%S")
    scriptname = sys.argv[0].split('/')[-1]
    streams = []

    try:
        #log_file = os.environ.get("LECHO_LOG")
        log_file = LIVECD_PARTITIONER_LOG

        if log_file != None:
            stream = open(log_file, "a")
            print >> stream, "%s [%s] - %s" % (date, scriptname, msg)
            stream.close()

    except:
        pass
# llecho()

def run(cmd):
    """
    Runs the passed command line, writes its exit status and output at the log
    and returns the exit status

    @type  cmd: basestring
    @param cmd: command line to be run

    @rtype: int
    @returns: exit status
    """
    # log command line
    llecho("Running: %s" % cmd)

    # run it
    status, output = getstatusoutput(cmd)
    status = status >> 8

    # log exit status and output
    llecho("Status: %d" % status)
    llecho("Output:\n%s\n" % output)

    # return exit status
    return status
# run()
