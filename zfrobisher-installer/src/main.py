#!/usr/bin/env python
#
# IMPORTS

from model.model import Model
from viewer.newtviewer import NewtViewer
from controller.controller import Controller

#
# CODE
#
def main():
    """
    KoP entry point
    """
    # create the viewer
    # TODO: create a factory for viewer
    viewer = NewtViewer()


    # create the model
    model = Model()

    # create the controller
    cont = Controller(model, viewer)

    cont.loop()

    # close the viewer
    viewer.destructor()

# main()

main()
