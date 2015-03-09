#!/usr/bin/python

#
# IMPORTS
#
import sys

from snack import *
from ui.backend import env as Env
from ui.systemupdate.updateprogress import UpdateProgress


#
# CONSTANTS
#


#
# CODE
#
if __name__ == "__main__":
    Env.set('systemupdate.disk', sys.argv[1])
    Env.set('systemupdate.filesystem', sys.argv[2])

    rc = -1

    while rc == -1:
        screen = SnackScreen()
        window = UpdateProgress(screen)
        rc = window.run()
        screen.finish()
