#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from subprocess import Popen, PIPE
from model.config import ZKVM_LOG_DIR

import logging
import os
import shutil
import traceback


#
# CODE
#
class ExecPostScripts(ScriptBase):
    """
    Execute post scripts provided in the kickstart file
    """

    def __init__(self):
        """
        Contructor.

        @rtype: None
        @return: Nothing
        """
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def onPostInstall(self, data):
        """
        Handles the post install event. Creates a mark file on installed and
        copy the log file from live image do installed system
        system.

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype: Nothing
        @return: Nothing
        """
        try:
            postScriptKS = ZKVM_LOG_DIR + '/%spostScriptKS.sh'
            postScriptKSLog = ZKVM_LOG_DIR + '/%spostScriptKS.log'
            counter = 0
            for script in data['model'].get('postScripts'):
                self.__logger.info(script)
                systemDir = data['model'].get('mountDir') + ZKVM_LOG_DIR
                if not os.path.exists(systemDir):
                    os.makedirs(systemDir)
                fileName = postScriptKS % counter
                systemFileName = data['model'].get('mountDir') + fileName
                tempFileName = fileName
                copyFileName = systemFileName
                if script['inChroot']:
                    tempFileName = systemFileName
                    copyFileName = fileName

                # create post script
                with open(tempFileName, "w") as fd:
                    fd.write(script['script'])
                os.chmod(tempFileName, 0777)
                shutil.copy(tempFileName, copyFileName)

                # execute post script
                cmdPost = [script['interp'], fileName]
                if script['inChroot']:
                    cmdPost.insert(0, data['model'].get('mountDir'))
                    cmdPost.insert(0, 'chroot')
                proc = Popen(cmdPost, stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                # create post script log
                if out:
                    # log in the live image
                    logFileName = postScriptKSLog % counter
                    systemLogFileName = data['model'].get('mountDir') + logFileName
                    with open(logFileName, "w") as fd:
                        fd.write(out)
                    # copy live image log to installed system
                    shutil.copy(logFileName, systemLogFileName)

                if proc.returncode != 0:
                    self.__logger.critical("Failed to execute kickstart post-script (%s) (exit code = %s): %s" % (cmdPost, proc.returncode, err))
                    raise ZKVMError("POSTINSTALL", "EXECPOSTSCRIPT", "EXEC_POSTSCRIPT")

                counter += 1
        except ZKVMError as e:
            self.__logger.critical("Failed ExecPostScript module!")
            raise
        except Exception as e:
            self.__logger.critical("Failed ExecPostScript module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("POSTINSTALL", "EXECPOSTSCRIPT", "POST_MODULES")
    # onPostInstall()
# ExecPostScripts
