#!/usr/bin/python

#
# IMPORTS
#
from controller.zkvmerror import ZKVMError
from modules.scriptbase import ScriptBase
from subprocess import Popen, PIPE

import logging
import os
import re
import shutil
import subprocess
import traceback


#
# CONSTANTS
#
DEFAULT_TZ = "America/New_York"
ZONEINFO_FILE = "/usr/share/zoneinfo/zone.tab"
ZONEINFO_DIR = "/usr/share/zoneinfo/"


#
# CODE
#
class Timezone(ScriptBase):
    """
    Handles timezone functionalities
    """
    def __init__(self):
        """
        Constructor
        """
        self.__logger = logging.getLogger(__name__)
        self.__tz = None
        self.__mountDir = None
        self.__entries = self.__loadTimezones()
    # __init__()

    def __loadTimezones(self):
        """
        Loads all the timezones available

        @rtype: list
        @returns: list of timezones
        """
        try:
            fd = open(ZONEINFO_FILE)
            content = fd.readlines()
            fd.close()

            result = []

            for line in content:
                if line.startswith("#"):
                    continue

                parts = line.strip().split()

                if len(parts) < 3:
                    continue

                result.append(parts[2])

            result.sort()

            return result
        except Exception as e:
            self.__logger.critical("Failed to load Timezones list")
            raise ZKVMError("POSTINSTALL", "TIMEZONE", "TIMEZONE_LIST")
    # __loadTimezones()

    def getEntries(self):
        """
        Returns all the timezones available

        @rtype: list
        @returns: list of timezones available
        """
        return self.__entries
    # getEntries()

    def setTimezone(self, tz):
        """
        Sets timezone

        @type  tz: string
        @param tz: timezone

        @rtype: None
        @returns: nothing
        """
        if tz in self.__entries:
            self.__tz = tz
        else:
            self.__tz = DEFAULT_TZ
    # setTimezone()

    def writeConfig(self):
        """
        Write timezone configuration

        @rtype: None
        @returns: nothing
        """
        try:
            tzFile = os.path.join(ZONEINFO_DIR, self.__tz)
            localTimeFile = "/etc/localtime"
            if self.__mountDir:
                tzFile = self.__mountDir + tzFile
                localTimeFile = self.__mountDir + localTimeFile

            shutil.copy(tzFile, localTimeFile)
        except Exception as e:
            self.__logger.critical("Failed to write timezone configuration")
            self.__logger.critical("%s" % (e))
    # writeConfig()

    def setUTC(self, flag):
        """
        Write configuration file to tells UTC is being used or not

        @type  flag: boolean
        @param flag: True to use UTC, False otherwise

        @rtype: None
        @returns: nothing
        """
        try:

            adjtimeFile = "/etc/adjtime"
            if self.__mountDir:
                adjtimeFile = self.__mountDir + adjtimeFile

            fd = open(adjtimeFile)
            content = fd.read()
            fd.close()

            newContent = content

            if flag and not "UTC" in content:
                if "LOCAL" in content:
                    newContent = re.sub("LOCAL", "UTC", content)
                else:
                    newContent += "UTC\n"
            elif not "LOCAL" in content:
                if "UTC" in content:
                    newContent = re.sub("UTC", "LOCAL", content)
                else:
                    newContent += "LOCAL\n"

            fd = open(adjtimeFile, "w")
            fd.write(newContent)
            fd.close()
        except Exception as e:
            self.__logger.critical("Failed to write UTC configuration")
            raise ZKVMError("POSTINSTALL", "TIMEZONE", "UTC_CONF")
    # setUTC()

    def setDateTime(self, datetime):
        """
        Set date time of the system

        @type  datetime: datetime
        @param datetime: Date time

        @rtype: None
        @returns: nothing
        """

        year = datetime[0]
        day = datetime[1]
        month = datetime[2]
        hour = datetime[3]
        min = datetime[4]
        sec = datetime[5]

        # command to restore SELinux configurations
        cmd = "date -s '%s/%s/%s %s:%s:%s' > /dev/null" % (day, month,
            year, hour, min, sec)
        # SELinux restoration failed: error
        if subprocess.call(cmd, shell=True) != 0:
            self.__logger.critical("Error to set datetime using date")
            raise RuntimeError('Error to set datetime using date')

    def onPostInstall(self, data):
        """
        Handles the post install event

        @type  data: dict
        @param data: relevant arguments for that given event

        @rtype:   Nothing
        @returns: Nothing
        """
        try:
            tz = data['model'].get('tz')
            isUTC = data['model'].get('isUTC')
            self.__mountDir = data['model'].get('mountDir')
            self.__datetime = data['model'].get('datetime')
            self.__logger.info('Datetime saved: %s' % self.__datetime)
            if tz:
                self.setTimezone(tz)
                self.writeConfig()
                self.setUTC(isUTC)
                if self.__datetime:
                    self.setDateTime(self.__datetime)
            else:
                self.__logger.critical("Failed to set timezone (%s)" % tz)
        except ZKVMError:
            self.__logger.critical("Failed Timezone module")
            raise
        except Exception as e:
            self.__logger.critical("Failed Timezone module")
            self.__logger.critical("EXCEPTION:" + str(type(e)))
            self.__logger.critical(str(e))
            self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
            raise ZKVMError("PREINSTALL", "TIMEZONE", "PRE_MODULES")
    # onPostInstall()
# Timezone
