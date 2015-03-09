#!/usr/bin/python

#
# IMPORTS
#
import os

from snack import *
from model.config import STR_VERSION
from viewer.__data__ import PREPARING_TO_INSTALL_IBM_ZKVM
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import WORKING
from viewer.__data__ import ERROR_INSTALLATION
from viewer.__data__ import ERROR_INSTALLATION_MSG
from viewer.__data__ import OK


#
# CONSTANTS
#

#
# CODE
#
class InstallProgress:
    """
    Install zKVM into the disk
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__total = 0

        self.__screen = screen
        self.__progressBar = Scale(self.__screen.width-35, 100)
        self.__msg = TextboxReflowed(self.__screen.width-30,
                PREPARING_TO_INSTALL_IBM_ZKVM.localize())

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__progressBar, 0, 0)
        self.__grid.add(self.__msg, 0, 1, (0, 1, 0, 0))

        self.__grid.draw()
        self.__screen.refresh()

        self.__downloadingPackages = 1
        self.__installingPackages = 1
        self.__progressPackages = 0
    # __init__()

    def setMessage(self):
        """
        Update message in the screen

        @rtype: None
        @returns: nothing
        """
        try:
            fd = open(OPERATION_INFO)
            msg = fd.read()
            fd.close()

            self.__msg.setText(msg)

        except IOError:

            self.__msg.setText("")
    # setMessage()

    def setMyMessage(self, msg, progress):
        """
        Update message in the screen

        @rtype: None
        @returns: nothing
        """
        self.__msg.setText(msg)

        self.__total = int(progress*0.8 + 10)
        self.__progressBar.set(self.__total)

        self.__grid.draw()
        self.__screen.refresh()
    # setMyMessage()

    def updateProgress(self, message, value):
        """
        Updates the progress bar

        @type  message: str
        @param message: message to be displayed in progress box

        @type  value: int
        @param value: value to update the bar

        @rtype: nothing
        @returns: nothing
        """
        self.__msg.setText(message)
        self.__progressBar.set(value)
        self.__grid.draw()
        self.__screen.refresh()
    # updateProgress()

    def setProgress(self):
        """
        Update progress value

        @rtype: None
        @returns: nothing
        """
        try:
            fd = open(OPERATION_PROGRESS)
            value = fd.read()
            fd.close()

            if value != "":
                self.__total = int(value)

        except IOError:

            self.__total = 0
    # setProgress

    def installInfo(self, data):
        """
        Callback to show install info progress
        """

        msg = ""

        # get operation from backend
        operation = str(data.get('operation', "Working"))

        #get the number of total package
        total_pkgs = int(data.get('total_pkgs',500))

        #get the progress of downloading packages
        download_pkgs = "(" + str(self.__downloadingPackages) + "/" + str(total_pkgs) + ")"

        #get the progress of installing packages
        install_pkgs = "(" + str(self.__installingPackages) + "/" + str(total_pkgs) + ")"

        # download
        if operation.startswith('download'):
            msg = "Downloading...: " + download_pkgs + " %s" % data['package']
            if operation == 'download-finish':
                self.__downloadingPackages += 1
                self.__progressPackages += 1

        # install-start
        elif operation == 'install-start':
            msg = "Installing...: " + install_pkgs + " [0%%] %s" % data['package']

        # install
        elif operation == 'install':
            msg = "Installing...: " + install_pkgs + "  [%s%%] %s" % (str(round(data['percent'], 2)), data['package'])

        # install-finish
        elif operation == 'install-finish':
            msg = "Installing...: " + install_pkgs + " [100%%] %s" % data['package']
            self.__installingPackages += 1
            self.__progressPackages += 1
        else:
            msg = WORKING.localize()


        progress_pkgs = 2*total_pkgs
        # calculate progress
        progress = int(float(float(self.__progressPackages)/float(progress_pkgs)) * 100)

        self.setMyMessage(msg, progress)
    # installInfo()

    def showGeneralError(self):
        """
        Displays an error when there is any error during installation

        @rtype: nothing
        @returns: nothing
        """
        ButtonChoiceWindow(self.__screen, ERROR_INSTALLATION.localize(),
                           ERROR_INSTALLATION_MSG.localize(),
                           buttons=[(OK.localize(), 'ok')],
                           width=50)
    # showErrorLength()

# InstallProgress
