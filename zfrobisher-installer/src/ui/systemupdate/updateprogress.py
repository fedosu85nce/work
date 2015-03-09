#!/usr/bin/python

#
# IMPORTS
#
import os
import shutil
import threading

from snack import *
from time import sleep
from ui.backend import env as Env
from ui.backend.updatefunctions import createWorkDirectory, setupzKVMRepo
from ui.backend.updatefunctions import  updateSystem, updateYabootFile
from ui.backend.updatefunctions import cpyRootfsToDisk, restoreCowPartition
from ui.config import *
from ui.default.rebootsystem import RebootSystem


#
# CONSTANTS
#
ERROR_MSG = "Could not update your zKVM system."


#
# CODE
#
class UpdateProgress:
    """
    Update zKVM into the disk
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__total = 0
        self.__dev = Env.get('systemupdate.disk')

        self.__screen = screen
        self.__progressBar = Scale(self.__screen.width-35, 100)
        self.__msg = TextboxReflowed(self.__screen.width-30, "Preparing system to update zKVM")

        self.__grid = GridForm(self.__screen, "IBM zKVM", 1, 3)
        self.__grid.add(self.__progressBar, 0, 0)
        self.__grid.add(self.__msg, 0, 1, (0, 1, 0, 0))
    # __init__()

    def setMessage(self):
        """
        Update message in the screen

        @rtype: None
        @returns: nothing
        """
        fd = open(OPERATION_INFO)
        msg = fd.read()
        fd.close()

        self.__msg.setText(msg)
    # setMessage()

    def setProgress(self):
        """
        Update progress value

        @rtype: None
        @returns: nothing
        """
        fd = open(OPERATION_PROGRESS)
        value = fd.read()
        fd.close()

        if value != "":
            self.__total = int(value)
    # setProgress

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        self.__grid.draw()
        self.__screen.refresh()

        sleep(2)

        self.__total = 3

        # start thread to do the job
        t = UpdateProcess(self.__dev)
        t.start()

        # update screen while the updating is being done
        while t.isAlive():
            if os.path.exists(OPERATION_INFO):
                self.setMessage()

            if os.path.exists(OPERATION_PROGRESS):
                self.setProgress()

            self.__progressBar.set(self.__total)
            self.__screen.refresh()
            sleep(1)

        if os.path.exists(OPERATION_INFO):
            os.remove(OPERATION_INFO)

        if os.path.exists(OPERATION_PROGRESS):
            os.remove(OPERATION_PROGRESS)

        # update successfully completed: update screen
        if os.path.exists(OPERATION_COMPLETED):
            self.__msg.setText("zKVM update successfully completed")
            self.__progressBar.set(100)
            self.__screen.refresh()
            sleep(2)

            os.remove(OPERATION_COMPLETED)

            window = RebootSystem(SnackScreen(), "The system was successfully updated.")
            rc = window.run()

            return 0

        # update failed: update screen
        if os.path.exists(OPERATION_FAILED):
            fd = open(OPERATION_FAILED)
            error = fd.read()
            fd.close()

            os.remove(OPERATION_FAILED)

            ButtonChoiceWindow(self.__screen, "Update Error",
                               error + "\n" + ERROR_MSG, buttons=["OK"], width = 50)

            return 0
    # run()
# UpdateProgress

class UpdateProcess(threading.Thread):
    """
    Thread to update zKVM into the disk
    """

    def __init__(self, dev):
        """
        Constructor

        @type  dev: string
        @param dev: disk used during the update
        """
        threading.Thread.__init__(self)

        self.__dev = dev
        self.__progress = 0
    # __init__()

    def info(self, msg):
        """
        Set information message

        @type  msg: string
        @param msg: information message

        @rtype: None
        @returns: nothing
        """
        fd = open(OPERATION_INFO, "w")
        fd.write(msg)
        fd.close()
    # info()

    def error(self, msg):
        """
        Set error message

        @type  msg: string
        @param msg: error message

        @rtype: None
        @returns: nothing
        """
        restoreCowPartition(self.__dev)

        fd = open(OPERATION_FAILED, "w")
        fd.write(msg)
        fd.close()
    # error()

    def success(self):
        """
        Write success file

        @rtype: None
        @returns: nothing
        """
        fd = open(OPERATION_COMPLETED, "w")
        fd.close()
    # success()

    def setProgress(self, value):
        """
        Set progress value

        @type  value: interger
        @param value: progress value

        @rtype: None
        @returns: nothing
        """
        fd = open(OPERATION_PROGRESS, "w")
        fd.write(str(value))
        fd.close()
    # setProgress

    def run(self):
        """
        Update zKVM into the disk

        @rtype: None
        @returns: nothing
        """
        # Create work directory
        # It will be the union between the squashfs image and the cow partition
        newRootPartition, directory = createWorkDirectory(self.__dev)
        self.__progress += 13
        self.setProgress(self.__progress)
        if (directory is None) or (newRootPartition is None):
            self.error("Error while creating work directory")
            return

        # Setup zKVM repo
        self.info("Setting up the zKVM YUM repository")
        rc = setupzKVMRepo(directory)
        self.__progress += 8
        self.setProgress(self.__progress)
        if not rc:
            self.error("Error while setting up the zKVM YUM repository")
            shutil.rmtree(directory, ignore_errors=True)
            return

        # Update system
        self.info("Updating zKVM packages")
        rc = updateSystem(directory, newRootPartition)
        self.__progress += 25
        self.setProgress(self.__progress)
        if not rc:
            self.error("Error while updating zKVM packages")
            shutil.rmtree(directory, ignore_errors=True)
            return

        # Copy root file system into the disk
        self.info("Updating zKVM system in disk %s..." % self.__dev)
        rc = cpyRootfsToDisk(newRootPartition)
        self.__progress += 21
        self.setProgress(self.__progress)
        if not rc:
            self.error("Error while updating zKVM")
            shutil.rmtree(directory, ignore_errors=True)
            return

        # Update /etc/yaboot.conf file
        self.info("Updating configuration files...")
        rc = updateYabootFile(newRootPartition)
        self.__progress += 26
        self.setProgress(self.__progress)
        if not rc:
            self.error("Error while updating /etc/yaboot.conf file")
            shutil.rmtree(directory, ignore_errors=True)
            return

        self.success()
    # run()
# UpdateProcess
