#!/usr/bin/env python

#
# IMPORTS
#
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED
from viewer.__data__ import IBMZKVMERROR_UNKNOWN
from viewer.__data__ import IBMZKVMERROR_DISK_SIZE
from viewer.__data__ import IBMZKVMERROR_NO_DISK
from viewer.__data__ import IBMZKVMERROR_ENTITLEMENT
from viewer.__data__ import IBMZKVMERROR_INSTALL_SYSTEM
from viewer.__data__ import IBMZKVMERROR_FORMATING_DISK
from viewer.__data__ import IBMZKVMERROR_ERROR
from viewer.__data__ import IBMZKVMERROR_DELETE_ENTITIES
from viewer.__data__ import IBMZKVMERROR_DEACTIVATE_VG
from viewer.__data__ import IBMZKVMERROR_STOP_SWRAID
from viewer.__data__ import IBMZKVMERROR_INFORMATION
from viewer.__data__ import IBMZKVMERROR_DELETE_PARTITIONS
from viewer.__data__ import IBMZKVMERROR_CREATE_PARTITIONS
from viewer.__data__ import IBMZKVMERROR_CREATE_LVM
from viewer.__data__ import IBMZKVMERROR_DOWNLOAD_HTTP
from viewer.__data__ import IBMZKVMERROR_DOWNLOAD_TFTP
from viewer.__data__ import IBMZKVMERROR_DOWNLOAD_NFS
from viewer.__data__ import IBMZKVMERROR_PARSER_FILE
from viewer.__data__ import IBMZKVMERROR_RAID_GET_LABEL
from viewer.__data__ import IBMZKVMERROR_PRE_MODULES
from viewer.__data__ import IBMZKVMERROR_RAID_SET_LABEL
from viewer.__data__ import IBMZKVMERROR_EXEC_PRESCRIPT
from viewer.__data__ import IBMZKVMERROR_EXEC_PRESCRIPT_ZKVM
from viewer.__data__ import IBMZKVMERROR_POST_MODULES
from viewer.__data__ import IBMZKVMERROR_ROOT_PWD_MANUAL
from viewer.__data__ import IBMZKVMERROR_EXEC_POSTSCRIPT
from viewer.__data__ import IBMZKVMERROR_NTP_SET
from viewer.__data__ import IBMZKVMERROR_INVALID_NIC
from viewer.__data__ import IBMZKVMERROR_NO_NIC
from viewer.__data__ import IBMZKVMERROR_NO_DISK_KS
from viewer.__data__ import IBMZKVMERROR_INSTALL_MSG
from viewer.__data__ import IBMZKVMERROR_NO_REPO
from viewer.__data__ import IBMZKVMERROR_INVALID_REPO
from viewer.__data__ import IBMZKVMERROR_INVALID_REPO_CONTENT
from viewer.__data__ import IBMZKVMERROR_TIMEZONE_LIST
from viewer.__data__ import IBMZKVMERROR_UTC_CONF
from viewer.__data__ import IBMZKVMERROR_ENTITLE_FW
from viewer.__data__ import IBMZKVMERROR_ENTITLE_MACHINE
from viewer.__data__ import IBMZKVMERROR_ENTITLE_HYPER
from viewer.__data__ import IBMZKVMERROR_NO_PREINSTALL
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_PARTITIONER
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_PACKAGES
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_POSTINSTALL
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_AUTOINSTALL
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_GETDISKS
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_DISKSEL
from viewer.__data__ import IBMZKVMERROR_UNEXPECTED_SYSCONF


#
# CONSTANTS
#
IBMZKVM_PREFIX = "IBMZKVM"


#
# CODE
#
class ZKVMError(Exception):
    """
    USAGE:
    =====
        * Raise:
          -----
            from controller.zkvmerror import ZKVMError
            import traceback

            try:
                <code...>
            except Exception as e:
                self.__logger.critical("Failed NetworkTopology module")
                self.__logger.critical("EXCEPTION:" + str(type(e)))
                self.__logger.critical(str(e))
                self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
                raise ZKVMError("PREINSTALL", "NETWORKTOPOLOGY", "NO_DISK")

        * Handle:
          ------
            from controller.zkvmerror import ZKVMError
            import traceback

            + General use case:
              ----------------
            try:
                <code...>
            except ZKVMError as e:
                raise
            except Exception as e:
                self.__logger.critical("Unexpected error")
                self.__logger.critical("EXCEPTION:" + str(type(e)))
                self.__logger.critical(str(e))
                self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
                raise ZKVMError("CONTROLLER", "UNKOWN", "UNEXPECTED")

            + Entry points (just only __init__() and loop()):
              ----------------------------------------------
            except ZKVMError as e:
                self.__logger.critical("ZKVMError: %s" % e.getLogCode(e.args))
                self.__createLog()
                self.__viewer.getGeneralTopError().run(e.getCode(e.args))
                self.rebootSystem(True)
            except Exception as e:
                self.__logger.critical("Unexpected error")
                self.__logger.critical("EXCEPTION:" + str(type(e)))
                self.__logger.critical(str(e))
                self.__logger.critical("Stacktrace:" + str(traceback.format_exc()))
                zkvmError = ZKVMError()
                unexpectedCode = zkvmError.getUnexpectedCode("CONTROLLER", "INIT")
                self.__logger.critical("ZKVMError: %s" % zkvmError.getLogCode(unexpectedCode[0]))
                self.__createLog()
                self.__viewer.getGeneralTopError().run(unexpectedCode)
                self.rebootSystem(True)
    """

    loc = {
        "CONTROLLER": "CO",
        "PARTITIONER": "PA",
        "INSTALLER": "IN",
        "PREINSTALL": "PR",
        "POSTINSTALL": "PO",
        "ERROR": "ZZ",  # Must *NOT* be used!!! Reserved for ZKVMError use only.
    }
    subLoc = {
        "UNKOWN": "00",
        "INIT": "01",
        "AUTOINSTALL": "02",
        "DISKSEL": "03",
        "INSTALLPROGRESS": "04",
        "LOOP": "05",
        "SYSCONF": "06",
        "GETDISKS": "07",
        "GET_PREV_INST": "08",
        "REINSTALL": "09",
        "INSTALLPROGRESSPARTITIONER": "10",
        "INSTALLPROGRESSPACKAGES": "11",
        "INSTALLPROGRESSPOSTINSTALL": "12",
        "GETDISKBYID": "13",
        "GETDISKBYLABEL": "14",
        "GETDISKAUTOINSTALL": "15",
        "LVM": "30",
        "RAID": "31",
        "DISK": "32",
        "CONVENTIONAL": "33",
        "FORMAT": "34",
        "INSTALLAUTO": "40",
        "EXECPRESCRIPT": "41",
        "IDSYSTEM": "42",
        "AUTOMOUNTER": "43",
        "ROOTPASSWORD": "44",
        "NETSETUP": "45",
        "DNS": "46",
        "NTP": "47",
        "EXECPOSTSCRIPT": "48",
        "FINALSETUP": "49",
        "SELINUXRELABELFS": "50",
        "AUTOUMOUNTER": "51",
        "NETWORKTOPOLOGY": "52",
        "NETDEV": "53",
        "TIMEZONE": "54",
        "INSTALLSYSTEM": "70",
        "INSTALLPACKAGES": "71",
        "ERROR": "99",  # Must *NOT* be used!!! Reserved for ZKVMError use only.
    }

    def __getLocationCode(self, code):
        """
        Return location code

        @type code: str
        @param code: string with location

        @rtype str
        @returns: location code
        """
        return self.loc.get(code) if self.loc.get(code) else self.loc.get("ERROR")
    # __getLocationCode()

    def __getSubLocationCode(self, code):
        """
        Return sublocation code

        @type code: str
        @param code: string with sublocation

        @rtype str
        @returns: sublocation code
        """
        return self.subLoc.get(code) if self.subLoc.get(code) else self.subLoc.get("ERROR")
    # __getSubLocationCode()

    def __getError(self):
        """
        Return error code dict

        @rtype dict
        @returns: error code dict
        """
        em = {
            "UNEXPECTED": ("000", IBMZKVMERROR_UNEXPECTED.localize()),
            "UNKNOWN": ("001", IBMZKVMERROR_UNKNOWN.localize()),
            "DISK_SIZE": ("002", IBMZKVMERROR_DISK_SIZE.localize()),
            "NO_DISK": ("003", IBMZKVMERROR_NO_DISK.localize()),
            "ENTITLEMENT": ("004", IBMZKVMERROR_ENTITLEMENT.localize()),
            "INSTALL_SYSTEM": ("005", IBMZKVMERROR_INSTALL_SYSTEM.localize()),
            "FORMATING_DISK": ("006", IBMZKVMERROR_FORMATING_DISK.localize()),
            "NO_PREINSTALL": ("007", IBMZKVMERROR_NO_PREINSTALL.localize()),
            "UNEXPECTED_PARTITIONER": ("008", IBMZKVMERROR_UNEXPECTED_PARTITIONER.localize()),
            "UNEXPECTED_PACKAGES": ("009", IBMZKVMERROR_UNEXPECTED_PACKAGES.localize()),
            "UNEXPECTED_POSTINSTALL": ("010", IBMZKVMERROR_UNEXPECTED_POSTINSTALL.localize()),
            "UNEXPECTED_AUTOINSTALL": ("011", IBMZKVMERROR_UNEXPECTED_AUTOINSTALL.localize()),
            "UNEXPECTED_GETDISKS": ("012", IBMZKVMERROR_UNEXPECTED_GETDISKS.localize()),
            "UNEXPECTED_DISKSEL": ("013", IBMZKVMERROR_UNEXPECTED_DISKSEL.localize()),
            "UNEXPECTED_SYSCONF": ("014", IBMZKVMERROR_UNEXPECTED_SYSCONF.localize()),
            "DELETE_ENTITIES": ("301", IBMZKVMERROR_DELETE_ENTITIES.localize()),
            "DEACTIVATE_VG": ("302", IBMZKVMERROR_DEACTIVATE_VG.localize()),
            "STOP_SWRAID": ("303", IBMZKVMERROR_STOP_SWRAID.localize()),
            "INFORMATION": ("304", IBMZKVMERROR_INFORMATION.localize()),
            "DELETE_PARTITIONS": ("305", IBMZKVMERROR_DELETE_PARTITIONS.localize()),
            "CREATE_PARTITIONS": ("306", IBMZKVMERROR_CREATE_PARTITIONS.localize()),
            "CREATE_LVM": ("307", IBMZKVMERROR_CREATE_LVM.localize()),
            "DOWNLOAD_HTTP": ("400", IBMZKVMERROR_DOWNLOAD_HTTP.localize()),
            "DOWNLOAD_TFTP": ("401", IBMZKVMERROR_DOWNLOAD_TFTP.localize()),
            "DOWNLOAD_NFS": ("402", IBMZKVMERROR_DOWNLOAD_NFS.localize()),
            "PARSER_FILE": ("403", IBMZKVMERROR_PARSER_FILE.localize()),
            "RAID_GET_LABEL": ("404", IBMZKVMERROR_RAID_GET_LABEL.localize()),
            "PRE_MODULES": ("405", IBMZKVMERROR_PRE_MODULES.localize()),
            "RAID_SET_LABEL": ("406", IBMZKVMERROR_RAID_SET_LABEL.localize()),
            "EXEC_PRESCRIPT": ("407", IBMZKVMERROR_EXEC_PRESCRIPT.localize()),
            "EXEC_PRESCRIPT_ZKVM": ("408", IBMZKVMERROR_EXEC_PRESCRIPT_ZKVM.localize()),
            "POST_MODULES": ("409", IBMZKVMERROR_POST_MODULES.localize()),
            "ROOT_PWD_MANUAL": ("410", IBMZKVMERROR_ROOT_PWD_MANUAL.localize()),
            "EXEC_POSTSCRIPT": ("411", IBMZKVMERROR_EXEC_POSTSCRIPT.localize()),
            "NTP_SET": ("411", IBMZKVMERROR_NTP_SET.localize()),
            "INVALID_NIC": ("412", IBMZKVMERROR_INVALID_NIC.localize()),
            "NO_NIC": ("413", IBMZKVMERROR_NO_NIC.localize()),
            "NO_DISK_KS": ("414", IBMZKVMERROR_NO_DISK_KS.localize()),
            "TIMEZONE_LIST": ("415", IBMZKVMERROR_TIMEZONE_LIST.localize()),
            "UTC_CONF": ("416", IBMZKVMERROR_UTC_CONF.localize()),
            "INSTALL_MSG": ("500", IBMZKVMERROR_INSTALL_MSG.localize()),
            "NO_REPO": ("501", IBMZKVMERROR_NO_REPO.localize()),
            "INVALID_REPO": ("502", IBMZKVMERROR_INVALID_REPO.localize()),
            "INVALID_REPO_CONTENT": ("503", IBMZKVMERROR_INVALID_REPO_CONTENT.localize()),
            "ENTITLE_FW": ("504", IBMZKVMERROR_ENTITLE_FW.localize()),
            "ENTITLE_MACHINE": ("505", IBMZKVMERROR_ENTITLE_MACHINE.localize()),
            "ENTITLE_HYPER": ("506", IBMZKVMERROR_ENTITLE_HYPER.localize()),
            "ERROR": ("999", IBMZKVMERROR_ERROR.localize()),  # Must *NOT* be used!!! Reserved for ZKVMError use only.
        }
        return em
    #__getError()

    def __getErrorCode(self, code):
        """
        Return error code

        @type code: str
        @param code: string with error

        @rtype str
        @returns: error code
        """
        em = self.__getError()
        return em.get(code)[0] if em.get(code) else em.get("ERROR")[0]
    # __getErrorCode()

    def __getErrorMessage(self, code):
        """
        Return error message

        @type code: str
        @param code: string with error

        @rtype str
        @returns: error message
        """
        em = self.__getError()
        return em.get(code)[1] if em.get(code) else em.get("ERROR")[1]
    # __getErrorMessage()

    def getCode(self, code):
        """
        Return external code

        @type code: str
        @param code: string with internal error code

        @rtype list
        @returns: external code + error message
        """
        locCode = self.__getLocationCode(code[0])
        subLocCode = self.__getSubLocationCode(code[1])
        errorCode = self.__getErrorCode(code[2])
        errorMsg = self.__getErrorMessage(code[2])
        retCode = IBMZKVM_PREFIX + locCode + subLocCode + errorCode
        retList = [retCode, errorMsg]
        return retList
    # getCode()

    def getLogCode(self, code):
        """
        Return code information to be sent to log

        @type code: str
        @param code: string with internal error code

        @rtype str
        @returns: code info for log
        """
        externalCode = self.getCode(code)
        internalCode = code
        retList = [externalCode, internalCode]
        return retList
    # getLogCode()

    def getUnexpectedCode(self, codeLoc="CONTROLLER", codeSubLoc="UNKNOWN"):
        """
        Return external code for unexpected exceptions

        @type codeLoc: str
        @param codeLoc: string with location
        @type codeSubLoc: str
        @param codeSubLoc: string with sublocation

        @rtype list
        @returns: external code + error message
        """
        return self.createCode(codeLoc, codeSubLoc, "UNEXPECTED")
    # getUnexpectedCode()

    def createCode(self, codeLoc="CONTROLLER", codeSubLoc="UNKNOWN", codeError="UNEXPECTED"):
        """
        Create external code

        @type codeLoc: str
        @param codeLoc: string with location
        @type codeSubLoc: str
        @param codeSubLoc: string with sublocation
        @type codeError: str
        @param codeError: string with error

        @rtype list
        @returns: external code + error message
        """
        code = [codeLoc, codeSubLoc, codeError]
        return self.getCode(code)
    # createCode()

    def translateCode(self, code):
        """
        Return internal code with error message

        @type code: str
        @param code: string with external error code

        @rtype str
        @returns: internal code + error message

        """
        retList = []
        if code.startswith(IBMZKVM_PREFIX):
            code = code[len(IBMZKVM_PREFIX):]
            locCode = code[:2]
            subLocCode = code[2:4]
            errorCode = code[4:]
            intLocCode = None
            intSubLocCode = None
            intErroCode = None
            errorMsg = None

            for key, value in self.loc.iteritems():
                if value == locCode:
                    intLocCode = key
                    break
            for key, value in self.subLoc.iteritems():
                if value == subLocCode:
                    intSubLocCode = key
                    break
            for key, value in self.subLoc.iteritems():
                if value[0] == errorCode:
                    intErroCode = key
                    errorMsg = value[1]
                    break
            retList = [intLocCode, intSubLocCode, intErroCode, errorMsg]
        return retList
    # translateCode()
