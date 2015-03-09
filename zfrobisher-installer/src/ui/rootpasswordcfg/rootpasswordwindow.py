#!/usr/bin/python

#
# IMPORTS
#
import os

from modules.rootpassword.rootpassword import RootPassword
from snack import *


#
# CONSTANTS
#
BUTTON_BACK="Back"
BUTTON_OK="OK"

ERROR_PASSWD_LENGTH="Password Length"
ERROR_PASSWD_LENGTH_MSG="The root password must be at least 6 characters long."
ERROR_PASSWD_MISMATCH="Password Mismatch"
ERROR_PASSWD_MISMATCH_MSG="The passwords you entered were different. Please try again."

PASSWD_CONFIRM_LABEL="Password (confirm):"
PASSWD_LABEL="Password:"

WINDOW_MSG="Pick a root password. You must type it twice to ensure you know what it is and didn't make a mistake in typing. Remember that the root password is a critical part of system security!"
WINDOW_TITLE="Root Password"


#
# CODE
#
class RootPasswordWindow:
    """
    Represents the root password screen
    """

    def __init__(self, screen):
        """
        Constructor

        @type  screen: SnackScreen
        @param screen: SnackScreen instance
        """
        self.__screen = screen

        self.__msg = TextboxReflowed(40, WINDOW_MSG)

        self.__buttonsBar = ButtonBar(self.__screen, [(BUTTON_OK, "ok"), ("Back", "back")])

        self.__passwd = Entry(24, "", password=1)
        self.__passwdConfirm = Entry(24, "", password=1)

        self.__passwdLabel = Label(PASSWD_LABEL)
        self.__passwdConfirmLabel = Label(PASSWD_CONFIRM_LABEL)

        self.__passwdGrid = Grid(2, 2)
        self.__passwdGrid.setField(self.__passwdLabel, 0, 0, anchorLeft=1)
        self.__passwdGrid.setField(self.__passwdConfirmLabel, 0, 1, anchorLeft=1)
        self.__passwdGrid.setField(self.__passwd, 1, 0)
        self.__passwdGrid.setField(self.__passwdConfirm, 1, 1)

        self.__grid = GridForm(self.__screen, WINDOW_TITLE, 1, 3)
        self.__grid.add(self.__msg, 0, 0)
        self.__grid.add(self.__passwdGrid, 0, 1, (0, 1, 0, 0))
        self.__grid.add(self.__buttonsBar, 0, 2, (0, 1, 0, 0))
    # __init__()

    def __show(self):
        """
        Shows screen once

        @rtype: integer
        @returns: status of operation
        """
        self.__grid.setCurrent(self.__passwd)
        self.__screen.refresh()
        result = self.__grid.run()

        rc = self.__buttonsBar.buttonPressed(result)

        if rc == "back":
            return -1

        if len(self.__passwd.value()) < 6:
            ButtonChoiceWindow(self.__screen, ERROR_PASSWD_LENGTH, 
                               ERROR_PASSWD_LENGTH_MSG, buttons=[BUTTON_OK], 
                               width=50)
        elif self.__passwd.value() != self.__passwdConfirm.value():
            ButtonChoiceWindow(self.__screen, ERROR_PASSWD_MISMATCH, 
                               ERROR_PASSWD_MISMATCH_MSG, buttons=[BUTTON_OK], 
                               width = 50)
        else:
            rootPass = RootPassword()
            rootPass.run(self.__passwd.value())

            return 0

        self.__passwd.set("")
        self.__passwdConfirm.set("")

        return 1
    # __show()
    
    def run(self):
        """
        Draws the screen

        @rtype: integer
        @returns: status of operation
        """
        rc = self.__show()

        while rc == 1:
            rc = self.__show()

        return rc
    # run()
# RootPasswordWindow
