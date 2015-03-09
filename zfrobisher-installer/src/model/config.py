# GA version
GA_VERSION = "1.1.0"

# KOP Build (in octal)
BUILD_NUMBER = 0

# KOP Respin
RESPIN = "0"

# KOP Version str
STR_VERSION = "%s" % (GA_VERSION)

# Project root path.
RUN_DIR = '/opt/ibm/zkvm-installer'

# Root filesystem image
ROOTFS_IMG = '/mnt/rootfs.img'

# New root filesystem image
NEW_ROOTFS_IMG = 'newrootfs.img'

# Error file: indicates the installation or update process failed
OPERATION_FAILED = '/opt/ibm/zkvm-installer/control/.install-failed'

# Information file: contains information about the installation or update process
OPERATION_INFO = '/opt/ibm/zkvm-installer/control/.install-info'

# Progress file: indicates the operation progress
OPERATION_PROGRESS = '/opt/ibm/zkvm-installer/control/.install-progress'

# Success file: indicates the operation successfully completes
OPERATION_COMPLETED = '/opt/ibm/zkvm-installer/control/.install-success'

# zKVM partition layout
PARTITION_LAYOUT = '/opt/ibm/zkvm-installer/ui/backend/config/partition.layout'

# zKVM functions
ZKVM_FUNCTIONS = '/opt/ibm/zkvm-installer/zkvm-functions'

# Path to default yaboot.conf file
DEFAULT_YABOOT_CONF = '/opt/ibm/zkvm-installer/config/yaboot.conf'

# path to tarball file that contains the zKVM repo
TARBALL_REPO = '/mnt/zkvm-repo.tar.gz'

# path to the zKVM repo
ZKVM_REPO = '/tmp/repo'

# Repo config
REPO_CONFIG = '/opt/ibm/zkvm-installer/config/zkvm.repo'

# Path to the script that update system packages
UPDATE_PKGS_SCRIPT = '/opt/ibm/zkvm-installer/ui/backend/updatepackages.py'

# Cow backup
COW_BACKUP = 'cow-bkp.tar.gz'

# zKVM logs directory
ZKVM_LOG_DIR = "/var/log/zkvm-installer"

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# LiveCD installer log
LIVECD_INSTALLER_LOG = "/tmp/installer.log"

# System image installer log
SYSIMG_INSTALLER_LOG = "%s/installer.log" % ZKVM_LOG_DIR

# LiveCD partitioner log
LIVECD_PARTITIONER_LOG = "/tmp/partitioner.log"

# System image partitioner log
SYSIMG_PARTITIONER_LOG = "%s/partitioner.log" % ZKVM_LOG_DIR

# IBMZKVM tarball log
IBMZKVM_TARBALL_ERROR_LOG = "/tmp/ibmzkvm_log.tar.gz"

# IBMZKVM tarball log
IBMZKVM_ERROR_LOG = "/tmp/ibmzkvm_error.log"

# Kickstart file
KICKSTART_FILE = "%s/kop.ks" % (ZKVM_LOG_DIR)
