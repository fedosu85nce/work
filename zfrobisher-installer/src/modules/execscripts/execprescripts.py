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
import traceback


#
# CODE
#
class ExecPreScripts(ScriptBase):
    """
    Execute pre scripts provided in the kickstart file
    """

    def __init__(self):
        """
        Contructor.

        @rtype: None
        @return: Nothing
        """
        self.__logger = logging.getLogger(__name__)
    # __init__()

    def __getIprRaidDisk(self, labelDisk):
        """
        Get the IPR RAID disk based on a label disk and create a new disklabel
        (partition table) on it

        @type  labelDisk: str
        @param labelDisk: IPR RAID disk label

        @rtype  : str
        @returns: path to IPR RAID disk
        """
        # FIXME: use the proper flag on iprconfig to get the
        # IPR RAID10 based on the given label
        #proc = Popen(['iprconfig', '-c', 'query-array-label', labelDisk, stdout = PIPE, stderr = PIPE)
        devLabel = "/dev/disk/by-label/%s" % labelDisk
        #proc = Popen(['realpath', devLabel], stdout = PIPE, stderr = PIPE)
        proc = Popen(['readlink', devLabel], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            self.__logger.critical("Failed to get device from label (%s) (exit code = %s): %s" % (devLabel, proc.returncode, err))
            raise ZKVMError("PREINSTALL", "EXECPRESCRIPT", "RAID_GET_LABEL")
        disk = out.rstrip()

        # Required to create a new disklabel (partition table)
        # for IPR-RAID otherwise it will fail to create the
        # partitions
        proc = Popen(['parted', '--script', '--align', 'optimal', disk, 'mklabel', 'msdos'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode != 0:
            self.__logger.critical("Failed to create a new disklabel (partition table) on  device %s (exit code = %s): %s" % (self.__data['disk'], proc.returncode, err))
            raise ZKVMError("PREINSTALL", "EXECPRESCRIPT", "RAID_SET_LABEL")

        return disk

    def onPreInstall(self, data):
        """
        Handles the pre install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype  : nothing
        @returns: nothing
        """
        try:
            #
            # kickstart pre scripts
            #
            preScriptKS = ZKVM_LOG_DIR + '/%spreScriptKS.sh'
            preScriptKSLog = ZKVM_LOG_DIR + '/%spreScriptKS.log'
            counter = 0
            for script in data['model'].get('preScripts'):
                fileName = preScriptKS % counter
                logFileName = preScriptKSLog % counter

                # create pre script
                with open(fileName, "w") as fd:
                    fd.write(script['script'])
                os.chmod(fileName, 0777)

                # execute pre script
                cmdPre = [script['interp'], fileName]
                proc = Popen(cmdPre, stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                # create pre script log
                if out:
                    with open(logFileName, "w") as fd:
                        fd.write(out)

                if proc.returncode != 0:
                    self.__logger.critical("Failed to execute kickstart pre-script (%s) (exit code = %s): %s" % (cmdPre, proc.returncode, err))
                    raise ZKVMError("PREINSTALL", "EXECPRESCRIPT", "EXEC_PRESCRIPT")

                counter += 1

            #
            # zKVM pre scripts
            #
            preScriptDir = "/opt/ibm/zkvm-installer/scripts/pre"
            preScriptFile = preScriptDir + "/%s"
            preScriptLog = ZKVM_LOG_DIR + "/%s.log"
            for script in os.listdir(preScriptDir):
                scriptName = preScriptFile % script
                scriptLog = preScriptLog % script

                # execute pre script
                proc = Popen([scriptName], stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                # create pre script log
                if out:
                    with open(scriptLog, "w") as fd:
                        fd.write(out)

                if proc.returncode != 0:
                    self.__logger.critical("Failed to execute zKVM pre-script (%s) (exit code = %s): %s" % (script, proc.returncode, err))
                    raise ZKVMError("PREINSTALL", "EXECPRESCRIPT", "EXEC_PRESCRIPT_ZKVM")

            # update disk device in case of manufacture mode
            #if data['model'].get('disk'):
            #    disk = data['model'].get('disk')
            #    if len(disk.split("=")) == 2 and disk.split("=")[0] == 'LABEL':
            #        disk = self.__getIprRaidDisk(disk.split("=")[1])
            #        data['model'].insert('disk', disk)

        except ZKVMError:
            self.__logger.critical("Failed ExecPreScript module!")
            raise
        except Exception as e:
            self.__logger.critical("Failed ExecPreScript module!")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "EXECPRESCRIPT", "PRE_MODULES")
    # onPreInstall()
# ExecPreScripts
