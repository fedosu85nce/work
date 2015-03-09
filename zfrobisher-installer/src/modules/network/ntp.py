#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase

import logging
import os
import traceback


#
# CONSTANTS
#
LOG_FILE_NAME = "/var/log/kop.log"
LOG_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

#
# CODE
#
class NTP(ScriptBase):
    """
    Edit the NTP configuration on the system
    """

    def __init__(self):
        """
        Constructor
        """
        logging.basicConfig(filename=LOG_FILE_NAME,
                            level=logging.DEBUG,
                           format=LOG_FORMATTER)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)
    # __init__()

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: None
        @returns: Nothing
        """
        try:

            serverList = data['model'].get('ntpservers')
            self.__logger.info("Server List: %s" % str(serverList))

            rootDir = data['model'].get('mountDir')

            # get etc directory from installed system
            etcDir = os.path.join(rootDir, 'etc/')

            ntp_file = os.path.join(etcDir, 'ntp.conf')

            # read ntp.conf file content from installed system to adjust it
            fd = open(ntp_file)
            content = fd.readlines()
            fd.close()

            # line just before where the list of server are
            ntp_mark = '# Please consider joining the pool (http://www.pool.ntp.org/join.html).\n'

            for i in content:
                # find the mark line
                if i == ntp_mark:
                    index = content.index(ntp_mark)

                    x = 1
                    # write the next server lines
                    for server in serverList:
                        content[index+x] = 'server '+server+' iburst\n'
                        x = x + 1

                    break

            # put the strings back together
            output = ""
            for i in content:
                output += i

            # update ntp.conf
            fd = open(ntp_file, "w")
            fd.write(output)
            fd.close()

        except Exception as e:
            self.__logger.critical("Failed NTP module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "NTP", "POST_MODULES")

    # onPostInstall()

