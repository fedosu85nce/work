#
# IMPORTS
#
from snack import *

#
# CONSTANTS
#
from viewer.__data__ import PART_BUTTON_OK

#
# CODE
#


def MsgBox(screen, title, msg):
    return ButtonChoiceWindow(screen,
                              title,
                              msg,
                              buttons=[PART_BUTTON_OK.localize()])
