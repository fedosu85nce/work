#
# IMPORTS
#
import os

from snack import *
from model.config import STR_VERSION
from viewer.__data__ import PREPARING_UPGRADE_SYSTEM
from viewer.__data__ import IBM_ZKVM
from viewer.__data__ import WORKING
from viewer.__data__ import YES
from viewer.__data__ import NO
from viewer.__data__ import OK

#
# CONSTANTS
#


#
# CODE
#
class UpgradeProgress:
    """
    Upgrade zKVM into the disk
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
                PREPARING_UPGRADE_SYSTEM.localize())

        self.__grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 3)
        self.__grid.add(self.__progressBar, 0, 0)
        self.__grid.add(self.__msg, 0, 1, (0, 1, 0, 0))

        self.__screen.refresh()

        self.__numberOfPackages = 100
        self.__installedPackages = 0
    # __init__()

    def showUpgrade(self):
        """
        Shows upgrade bar

        @rtype: nothing
        @returns: nothing
        """
        self.__grid.draw()
        self.__screen.refresh()
    def setNumberOfPackages(self, total):
        """
        Sets the total number of packages to be upgraded

        @type  total: int
        @param total: number of packages

        @rtype: nothing
        @returns: nothing
        """
        self.__numberOfPackages = total
    # setNumberOfPackages()

    def setMyMessage(self, msg, progress):
        """
        Update message in the screen

        @rtype: None
        @returns: nothing
        """
        self.__msg.setText(msg)

        self.__total = int((progress + 50) / 1.66)
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

    def upgradeInfo(self, data):
        """
        Callback to show upgrade info progress
        """
        msg = ""

        # get operation from backend
        operation = str(data.get('operation', "Working"))

        # install-start
        if operation == 'install-start':
            msg = "[0%%] %s" % data['package']

        # install
        elif operation == 'install':
            msg = "[%s%%] %s" % (str(round(data['percent'], 2)), data['package'])

        # install-finish
        elif operation == 'install-finish':
            self.__installedPackages += 1
            msg = "[100%%]: %s" % data['package']

        else:
            msg = WORKING.localize()

        # calculate progress
        progress = int(float(float(self.__installedPackages)/float(self.__numberOfPackages)) * 100)

        self.setMyMessage(msg, progress)
    # upgradeInfo()

    def showMessageBox(self, message):
        """
        Draws the message box

        @rtype:   nothing
        @returns: nothing
        """
        textBox = TextboxReflowed(len(message), message)
        okButtonBar = ButtonBar(self.__screen, [(OK.localize(), "ok")])

        grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 2)
        grid.add(textBox, 0, 0)
        grid.add(okButtonBar, 0, 1, (0, 1, 0, 0))

        grid.run()
        self.__screen.popWindow()
    # showMessageBox()

    def showConfirmationBox(self, message):
        """
        Draws the confirmation box and returns the selected button

        @rtype:   str
        @returns: True for 'YES', False for 'NO'
        """
        textBox = TextboxReflowed(len(message), message)
        buttonsBar = ButtonBar(self.__screen, [(YES.localize(), True), (NO.localize(), False)])

        grid = GridForm(self.__screen, IBM_ZKVM.localize() % STR_VERSION, 1, 2)
        grid.add(textBox, 0, 0)
        grid.add(buttonsBar, 0, 1, (0, 1, 0, 0))

        result = grid.run()
        self.__screen.popWindow()

        return buttonsBar.buttonPressed(result)
    # showConfirmationBox()

# UpgradeProgress
