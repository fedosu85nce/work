# -*- coding: utf-8 -*-
from modules.i18n.i18n import _

#
# CONSTANTS
#


#
# menu
#
WELCOME_IBM_ZKVM = _("Welcome to IBM zKVM %s")
SELECT_ONE_OF_THE_OPTIONS_BELOW = _("Select one of the options below and follow the instructions.")
ARE_YOU_SURE_YOU_WANTO_TO = _("Are you sure you want to install on device %s?\n\n \
The following partitions will be removed: %s\n\n \
The following LVMs will be removed: %s\n\n")
IBM_ZKVM = _("IBM zKVM %s")
OK = _("Ok")
BACK = _("Back")
SKIP = _("Skip")
NEXT = _("Next")
EDIT = _("Edit")
HELP_LINE = _("  <Tab>/<Shift-Tab> between elements   |  <Space> selects")


#
# rootchangepassword screen
#
ERROR_PASSWD_LENGTH = _("Password Length")
ERROR_PASSWD_LENGTH_MSG = _("The root password must be at least 6 characters long.")
ERROR_PASSWD_MISMATCH = _("Password Mismatch")
ERROR_PASSWD_MISMATCH_MSG = _("The passwords you entered were different. Please try again.")
PASSWD_CONFIRM_LABEL = _("Password (confirm):")
PASSWD_LABEL = _("Password:")
PASSWD_WINDOW_MSG = _("Set the root password. The root password requires confirmation to ensure it was entered correctly. Remember that the root password is a critical part of system security!")
PASSWD_WINDOW_TITLE = _("Root Password")

#
# timezone screen
#
TIMEZONE_LABEL = _("Select the timezone for the system")
TIMEZONE_UTC_CHECKBOX_LABEL = _("System clock uses UTC")
TIMEZONE_SELECTION_LABEL = _("Timezone Selection")

#
# listnetworkifaces screen
#
LISTNETIFACE_SELECT_DEVICE = _("Select the device to be configured:")
LISTNETIFACE_CONFIG_NET = _("Configure network")
UP = _("UP")
DOWN = _("DOWN")

#
# dnssetup screen
#
DNSSETUP_HOSTNAME_LABEL = _("Hostname")
DNSSETUP_FST_DNS_LABEL = _("Primary DNS")
DNSSETUP_SND_DNS_LABEL = _("Secondary DNS")
DNSSETUP_SEARCH_LABEL = _("Search")
DNSSETUP_CONFIG_DNS = _("DNS Configuration")

#
# ntpsetup screen
#
NTPSETUP_CONFIG_NTP = _("NTP Configuration")
NTPSETUP_SERVER_1 = _("NTP server 1: ")
NTPSETUP_SERVER_2 = _("NTP server 2: ")
NTPSETUP_SERVER_3 = _("NTP server 3: ")
NTPSETUP_SERVER_4 = _("NTP server 4: ")
ENABLE_LABEL = _("Enable")

#
# datetime screen
#
DATE_TIME_SETUP = _("Date and time configuration")
DATE_LABEL = _("Date (YYYY / MM / DD):")
TIME_LABEL = _("Time (HH:MM:SS):")
ERROR_DATETIME_FORMAT = _("Date time error")
ERROR_DATETIME_FORMAT_MSG = _("Date or time format is not correct!\nThe input: %s\nCorrect format: YYYY/MM/DD HH:MM:SS")


#
# networkconfig screen
#
ERROR_INVALID_ENTRY= _("Invalid Entry")
ERROR_INVALID_ENTRY_MSG= _("Either DHCP must be selected, or IP must be provided.")
NETWORKCFG_DEVICE_LABEL = _("Device")
NETWORKCFG_MACADDR_LABEL = _("MAC Address")
NETWORKCFG_DHCP_LABEL = _("Use DHCP")
NETWORKCFG_IP_LABEL = _("Static IP")
NETWORKCFG_NETMASK_LABEL = _("Netmask")
NETWORKCFG_GATEWAY_LABEL = _("Default gateway IP")
NETWORKCFG_DEVICE_CONFIG = _("Network Device Configuration")
NETWORKCFG_BRIDGE_LABEL = _("Create Network bridge device (br%s)")

# checkharddisk
#
LVM_ERROR_MSG = _("Error while trying to remove the Volume Group in %s")
WARNING_MSG = _("The disk %s is part of the LVM Volume Group(s) ['VolGroup'] which will be destroyed if you continue. Are you sure you want to use that disk?")
YES = _("Yes")
NO = _("No")
INSTALLATION_ERROR = _("Installation Error")

#
# selectharddisk
#
SELECT_DEVICE_TO_INSTALL = _("Select the device to install IBM zKVM. All data on the selected disk will be lost.")
SELECT_TITLE = _("Disk information")
SELECT_HELP_LINE = _("  <Tab>/<Shift-Tab> between elements  |  <F3> for details")
ERROR_DISK_SIZE = _("Disk size")
ERROR_DISK_SIZE_MSG = _("The disk size must be greater than 70G!")
ERROR_NO_DISK_SELECTED = _("No disk selected")
ERROR_NO_DISK_SELECTED_MSG = _("No disk was selected. Please select at least one disk for installation.")
SELECT_ID = _("ID:")
SELECT_SIZE = _("Size")
SELECT_MULTIPATH = _("Multipath:")
SELECT_NAME = _("Name")
SELECT_FILESYSTEM = _("Filesystem")
SELECT_VGRAID = _("VG/Raid")
SELECT_ADD_ZFCP = _("Add zFCP")

#
# addzfcp
#
ADDZFCP_WINDOW_TITLE = _("Add zFCP")
ADDZFCP_MSG = _('You must provide the Device Number, WWPN and LUN configured for adding zFCP.')
DEVNO_LABEL = _("Device Number:")
WWID_LABEL = _("WWPN:")
LUNID_LABEL = _("LUN:")

#
# chooselanguage
#
CHOOSE_LANGUAGE = _("Choose the language")

#
# partition configure
#
# Reset form(Run form again after run)
PART_FORM_RESET = _("Reset")

# Partition method form
PART_TITLE_METHOD = _("Select Partition Method")
PART_LABEL_DISKDESC = _("Below are the disks you want to install on.")
PART_LABEL_PARTITIONING = _("Partitioning:")
PART_BUTTON_AUTO = _("Automatically")
PART_BUTTON_MANUAL = _("Manually")

# select disk for standard partition form
PART_TITLE_STDDESC = _("Please select the disk to be used as standard partition.")
PART_TITLE_STD = _("Standard Parition Disk Selection")

# select vg form
PART_TITLE_VG = _("Configure Volume Group")
PART_LABEL_VGDESC = _("Below is the information of already exist volume group.")
PART_LABEL_POLICY = _("Size Policy:")
PART_LABEL_NEWVG = _("NewVG")
PART_LABEL_FREE = _("Free:")

PART_POLICY_AUTO = _("Automatic")
PART_POLICY_MAX = _("Largest")
PART_POLICY_FIXED = _("Fixed")

PART_TITLE_PARM_ERR = _("Parameter Validation")
PART_ERR_VG_EMPTY_NAME = _("You must give a valid name for the new VG.")
PART_ERR_VG_EXIST = _("You can't create VG with name %s. It's already exist.")
PART_ERR_VG_NO_DISK = _("You must select at least one disk for the VG.")
PART_ERR_VG_NO_SIZE = _('You must give a valid size for policy "Fixed".')

# action list form
PART_TITLE_ACTION = _("SUMMARY OF CHANGES")
PART_LABEL_ACTIONDESC = _("Your customizations will result in \
    the following changes taking effect on the disks you've selected:")
PART_BUTTON_OK = _("OK")
PART_BUTTON_BACK = _("BACK")

# manual partition form
PART_TITLE_MANUAL = _("Manual Partitioning")
PART_LABEL_NAME = _("Name:")
PART_LABEL_MNT = _("Mount Point:")
PART_LABEL_LABEL = _("Label:")
PART_LABEL_CAP = _("Desired Capacity:")
PART_LABEL_TYPE = _("Device Type:")
PART_LABEL_FS = _("File System:")
PART_LABEL_AVAIL = _("Available:")
PART_LABEL_TOTAL = _("Total:")
PART_LABEL_LVM =_("Logical Volume")
PART_LABEL_STD = _("Standard Partition")
PART_BUTTON_ADD = _("ADD")
PART_BUTTON_DEL = _("DEL")
PART_BUTTON_MODIFY = _("MODIFY")
PART_BUTTON_DONE = _("DONE")

# new partition form
PART_TITLE_NEWPART = _("New Partition")
PART_PROMPT_NEWPART = _("/boot, / , and swap are essential partitions, make \
sure these have been configured.")
PART_FS_XFS = "xfs"
PART_FS_EXT3 = "ext3"
PART_FS_EXT4 = "ext4"
PART_FS_SWAP = "swap"

# partition interface
PART_TITLE_DISKERR = _("Select Disks Error")
PART_ERROR_NODISK = _("You must select at least one disk.")
PART_TITLE_DELPART_ERR = _("Delete Partition Error")
PART_TITLE_MANUALPART_ERR = _("Manual Partition Error")
PART_TITLE_MANUALPART_MISS_ESSENTIAL_PARTS = _("Miss some essential partitions")
PART_ERROR_DEL_REQUIRED = _("You can't delete the required partition: %s")
PART_ERROR_NOT_CONFIG = _("You must configure device for below partitions \
                through clicking Device Info button:\n")
PART_TITLE_VG_CONSISTENCY_CHECK = _("VG Consistency Check for Deletion")
PART_WARN_MSG_VG_CONSISTENCY_CHECK = _("These disks you have seleceted include \
Volume Group consisting of Physical Volumes also on the following disks:\n %22s \n\n\
which you have not chosen. This might cause the Logical Volumes on these disks \
unavailable, are you sure you will do this?\n\n")

# mountpoint validation
PART_MP_CHECK_TITLE = _("Mount Point Validation")
PART_MP_MSG_INUSE = _("That mount point is already in use. Try something else?")
PART_MP_MSG_NONE = _("Please enter a valid mount point.")
PART_MP_MSG_INSYS = _("That mount point is invalid. Try something else?")
PART_MP_MSG_ERR_FORMAT = _("That mount point is invalid fromat. Try something else?")

#
# confirmreinstall
#
WARNING_MSG = _("The current installed system will be erased, including all \
general system-wide and virtualization configuration files.\
Only the contents within /var/lib/libvirt/images and /var/log will be preserved. \
WARNING: this means the configuration of your Virtual Machines WILL BE ERASED, \
leaving only the disk images behind. You are advised to back up your VM \
configurations before proceeding. Are you sure you would like to proceed?")
REINSTALL_DISK_MSG = _("A previous installation of zKVM has been detected at:\n\n%s\n\n")
WARNING_MSG_MISS_ESSENTIAL_PART = _("You have not create \n\n%30s\n\n partition which is \
required by the system, you need to add it in the partition screen.")

#
# entitlementerror
#
ENTITLE_ERROR_MSG = _("Hardware is not entitled to proceed. Aborting!")
INVALID_ENTITLEMENT = _("Invalid entitlement! ")

#
# installprogress
#
PREPARING_TO_INSTALL_IBM_ZKVM = _("Preparing to install IBM zKVM System")
ERROR_INSTALLATION = _("Unknown error")
ERROR_INSTALLATION_MSG = _("Sorry something went wrong the proper error \
message is on the log file")

#
# rebootsystem
#
REBOOT_MSG = _("Please, reboot your system now.")
REBOOT = _("Reboot")
INSTALLATION_COMPLETED = _("Installation completed! ")

#
# reinstallerror
#
REINSTALL_ERROR_MSG = _("The reinstall process can't continue. No previous \
system was found. Aborting!")

#
# upgradeprogress
#
PREPARING_UPGRADE_SYSTEM = _("Preparing to upgrade system")
WORKING = _("Working...")

#
# ZKVM ERROR
#
ZKVM_ERROR_MSG = _("Installation exited with error code: %s")
ZKVM_LOG_MSG = _("Log is available on %s")
IBMZKVMERROR_UNEXPECTED = _("Unexpected error.")
IBMZKVMERROR_UNKNOWN = _("Unknown error.")
IBMZKVMERROR_DISK_SIZE = _("Invalid disk size.")
IBMZKVMERROR_NO_DISK = _("No disk found in the system.")
IBMZKVMERROR_ENTITLEMENT = _("Hardware is not entitled, aborting installation.")
IBMZKVMERROR_INSTALL_SYSTEM = _("Error while installing IBM zKVM.")
IBMZKVMERROR_FORMATING_DISK = _("Error while performing disk operations.")
IBMZKVMERROR_ERROR = _("Invalid error code.")
IBMZKVMERROR_DELETE_ENTITIES = _("Could not remove LVM entities.")
IBMZKVMERROR_DEACTIVATE_VG = _("Could not deactivate volume groups.")
IBMZKVMERROR_ACTIVATE_VG = _("Could not activate volume groups.")
IBMZKVMERROR_STOP_SWRAID = _("Could not stop software RAID.")
IBMZKVMERROR_INFORMATION = _("Disk information not available.")
IBMZKVMERROR_DELETE_PARTITIONS = _("Problem while removing pratitioning scheme.")
IBMZKVMERROR_CREATE_PARTITIONS = _("Problem while partitioning the disk.")
IBMZKVMERROR_CREATE_LVM = _("Problem while creating LVM.")
IBMZKVMERROR_DOWNLOAD_HTTP = _("Failed to download (HTTP) install automation file.")
IBMZKVMERROR_DOWNLOAD_TFTP = _("Failed to download (TFTP) install automation file.")
IBMZKVMERROR_DOWNLOAD_NFS = _("Problem downloading (NFS) install automation file.")
IBMZKVMERROR_PARSER_FILE = _("Could not parse install automation file.")
IBMZKVMERROR_RAID_GET_LABEL = _("Failed to get IPR RAID label.")
IBMZKVMERROR_PRE_MODULES = _("Failed while executing pre-install modules.")
IBMZKVMERROR_RAID_SET_LABEL = _("Failed to create disklabel on IPR RAID.")
IBMZKVMERROR_EXEC_PRESCRIPT = _("Failed to execute install automation pre-script.")
IBMZKVMERROR_EXEC_PRESCRIPT_ZKVM = _("Failed to execute zKVM pre-script.")
IBMZKVMERROR_POST_MODULES = _("Failed while executing post-install modules.")
IBMZKVMERROR_ROOT_PWD_MANUAL = _("Failed to set password.")
IBMZKVMERROR_EXEC_POSTSCRIPT = _("Failed to execute install automation post-script.")
IBMZKVMERROR_NTP_SET = _("Failed to set NTP service.")
IBMZKVMERROR_INVALID_NIC = _("Invalid network interface.")
IBMZKVMERROR_UTC_CONF= _("Failed to write UTC time configuration.")
IBMZKVMERROR_NO_NIC = _("Missing target network interface in install automation file.")
IBMZKVMERROR_NO_DISK_KS = _("Missing target disk parameter in install automation file.")
IBMZKVMERROR_INSTALL_MSG = _("Error while installing packages.")
IBMZKVMERROR_NO_REPO = _("No repository provided to the installer.")
IBMZKVMERROR_INVALID_REPO = _("Invalid repository path.")
IBMZKVMERROR_INVALID_REPO_CONTENT = _("Invalid repository content.")
IBMZKVMERROR_TIMEZONE_LIST = _("Failed to load Timezones list.")
IBMZKVMERROR_ENTITLE_FW = _("Firmware version must be greater than %s")
IBMZKVMERROR_ENTITLE_MACHINE = _("Invalid machine type.")
IBMZKVMERROR_ENTITLE_HYPER = _("Invalid hypervisor.")
IBMZKVMERROR_NO_PREINSTALL = _("No previous system found.")
IBMZKVMERROR_UNEXPECTED_PARTITIONER = _("Unexpected error while partitioning the disk.")
IBMZKVMERROR_UNEXPECTED_PACKAGES = _("Unexpected error while installing packages.")
IBMZKVMERROR_UNEXPECTED_POSTINSTALL = _("Unexpected error while executing post-install modules.")
IBMZKVMERROR_UNEXPECTED_AUTOINSTALL = _("Unexpected error while executing kickstart.")
IBMZKVMERROR_UNEXPECTED_GETDISKS = _("Unexpected error while verifying disks.")
IBMZKVMERROR_UNEXPECTED_DISKSEL = _("Unexpected error while selecting disks.")
IBMZKVMERROR_UNEXPECTED_SYSCONF = _("Unexpected error while configuring system.")

# installationsummary
#
INSTALLATION_SUMMARY = _("Installation Summary")
TIMEZONE = _("Timezone: ")
DATE_TIME =_("Date/Time: ")
NTP_SERVERS = _("NTP servers")
NTP_DISABLED = _("NTP disabled")
IP_ADDRESS = _("IP Address: ")
GATEWAY = _("Gateway: ")
NETMASK = _("Netmask: ")
HOSTNAME = _("Hostname: ")
BRIDGE = _("Bridge: ")
DHCP_IS_ENABLE = _("DHCP is enabled")
NETWORK = _("Network")
DEVICE = _("Device: ")
PASSWORD_IS_SET = _("Password is set")
SYSTEM_CLOCK_USES_UTC = _("System clock uses UTC: ")

# license window
LICENSE_BUTTON_ACCEPT = _("I Accept both IBM and non-IBM terms")
LICENSE_BUTTON_DECLINE = _("I do not accept the terms in the license agreement")

# interface config window
INTERFACE_DEVICE = _("Device")
ACTIVE_INTERFACE = _("Active Interface")
PORT_NAME_LABEL = _("Port Name")
LAYER2_LABEL = _("Layer2")
PORT_NUMBER_LABEL = _("Port Number")
INVALID_PORT_NUMBER = _("ERROR: Invalid port number value.")
PORT_NAME_TOO_LONE = _("ERROR: Port name is too long (0 to 8 character).")
INVALID_PORT_NAME = _("ERROR: Invalid character(s) in port name field.")
ONE_OR_MORE_FIELD_ERROR = _("One or more field error")
