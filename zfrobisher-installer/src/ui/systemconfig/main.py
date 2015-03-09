#!/usr/bin/python

#
# IMPORTS
#
from snack import *
from ui.datetimecfg.confirmdatetime import ConfirmDateTime
from ui.datetimecfg.listtimezones import ListTimezones
from ui.networkcfg.dnsconfig import DNSConfig
from ui.networkcfg.listnetinterfaces import ListNetInterfaces
from ui.systemconfig.configcompleted import ConfigCompleted
from ui.systemconfig.menu import Menu
from ui.rootpasswordcfg.rootpasswordwindow import RootPasswordWindow
from model.config import LIVECD_INSTALLER_LOG

import logging

#
# CONSTANTS
#
from ui.__data__ import ROOT_PASSWORD
from ui.__data__ import TIMEZONE_SELECTION
from ui.__data__ import DATE_AND_TIME
from ui.__data__ import CONFIGURE_NETWORK
from ui.__data__ import DNS_CONFIGURATION
from ui.__data__ import EXIT

#
# CODE
#
if __name__ == "__main__":
    logging.basicConfig(filename=LIVECD_INSTALLER_LOG, level=logging.DEBUG)


    # menu options

    menuOptions = []
    menuOptions.append((ROOT_PASSWORD.localize(),RootPasswordWindow))
    menuOptions.append((TIMEZONE_SELECTION.localize(),ListTimezones))
    menuOptions.append((DATE_AND_TIME.localize(),ConfirmDateTime))
    menuOptions.append((CONFIGURE_NETWORK.localize(),ListNetInterfaces))
    menuOptions.append((DNS_CONFIGURATION.localize(),DNSConfig))
    menuOptions.append((EXIT.localize(),ConfigCompleted))

    action= ""

    while action != 'exit':
        screen_menu = Menu((SnackScreen()))
        screen_menu.setMenuOptions(menuOptions)

        action_menu = screen_menu.run()
        action = action_menu(SnackScreen()).run()
