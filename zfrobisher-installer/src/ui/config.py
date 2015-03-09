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
PARTITION_LAYOUT= '/opt/ibm/zkvm-installer/ui/backend/config/partition.layout'

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
