#! /usr/bin/python

#
# IMPORTS
#
from pykickstart.parser import *
from pykickstart.version import makeVersion
from pykickstart.constants import *
from modules.scriptbase import ScriptBase
import logging
#
# CONSTANTS
#
DEFAULT_KICKSTART_FILE = '/opt/ibm/zkvm-installer/kickstart/customization.ks'

class ParseCustomizationKS(ScriptBase):
    """
    Insert pre-scripts and post-scripts in kickstart file into glable variable "data"
    """
    def __init__(self):
        """
        Constructor
        """
        self.__kickstartFile = DEFAULT_KICKSTART_FILE
        self.__data = {
            'preScripts': [],
            'postScripts': []
        }
        self.__logger = logging.getLogger(__name__)
    #__init__()
    def onPreInstall(self, data):
        """
        Handle the pre install event
        @type data: dict
        @param data: relevant arguments for that given event
        @rtype: nothing
        @returns: nothing
        """
        if data['model'].get('isKickstart'):
            return

        ksparser = KickstartParser(makeVersion())
        ksparser.readKickstart(self.__kickstartFile)
        for script in ksparser.handler.scripts:
            info = {}
            info['script'] = script.script
            info['interp'] = script.interp
            info['inChroot'] = script.inChroot
            info['errorOnFail'] = script.errorOnFail

            if script.type == constants.KS_SCRIPT_PRE:
                self.__data['preScripts'].append(info)
            if script.type == constants.KS_SCRIPT_POST:
                self.__data['postScripts'].append(info)
        self.__logger.info(self.__data)
        for key, value in self.__data.iteritems():
            data['model'].insert(key, value)
    #onPreInstall()
#ParseCustomizationKS
