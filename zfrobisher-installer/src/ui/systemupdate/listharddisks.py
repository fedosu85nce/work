#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from ui.backend import env as Env
from ui.backend.updatefunctions import getzKVMdisks


#
# CONSTANTS
#


#
# CODE
#
class ListHardDisks:
    """
    List all zKVM disks found in the system
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen
        self.__msg = TextboxReflowed(40, "The following disks seem to have zKVM installed. Select one to procedure with the update process.")
        self.__list = Listbox(5, returnExit=1)
        self.__buttonsBar = ButtonBar(self.__screen, [("OK", "ok"), ("Back", "back")])

        self.__grid = GridForm(self.__screen, "IBM zKVM", 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__list, 0, 1, (0, 1, 0, 0))
        self.__grid.add(self.__buttonsBar, 0, 2)
    # __init__()

    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: sucess status
        """
        devices = getzKVMdisks()

        for dev in devices:
            self.__list.append(dev, dev)

        result = self.__grid.run()
        self.__screen.popWindow()

        rc = self.__buttonsBar.buttonPressed(result)
        if rc == "back":
            return -1

        Env.set('systemupdate.disk', "/dev/%s" % self.__list.current())
        return 0
    # run()
# ListHardDisks
