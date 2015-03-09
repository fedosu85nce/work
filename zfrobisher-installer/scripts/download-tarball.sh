#! /bin/sh


# validate params
[ -z "$BUILD_ID" ]     && echo "ERROR: BUILD_ID cannot be empty"     && exit 255
[ -z "$SYMLINK_NAME" ] && echo "ERROR: SYMLINK_NAME cannot be empty" && exit 255


# create dir where downloaded files will reside
[ ! -d "$MCP_TARBALLS_DIR" ] && mkdir -p "$MCP_TARBALLS_DIR"


# form BUILD_ID2 according to BUILD_ID specified as a parameter for this job
BUILD_ID2="${BUILD_ID:0:4}-${BUILD_ID:4:2}-${BUILD_ID:6:2}-${BUILD_ID:9}"


# set urls
URL="${GSA_BASE_URL}/${BUILD_ID}"
RPMS_TARBALL_NAME="pkvm2_1_ppc64-f19-ppc64-mcp-${BUILD_ID2}-rpms.tar.gz"
RPMS_TARBALL_URL="${URL}/${RPMS_TARBALL_NAME}"
DEBUG_TARBALL_NAME="pkvm2_1_ppc64-f19-ppc64-mcp-${BUILD_ID2}-debuginfo_rpms.tar.gz"
DEBUG_TARBALL_URL="${URL}/${DEBUG_TARBALL_NAME}"
CHECKSUM_NAME="pkvm2_1_ppc64-f19-ppc64-mcp-${BUILD_ID2}-sha1sums.txt"
CHECKSUM_URL="${URL}/${CHECKSUM_NAME}"
FILE_NAMES="${RPMS_TARBALL_NAME} ${DEBUG_TARBALL_NAME} ${CHECKSUM_NAME}"
FILE_URLS="${RPMS_TARBALL_URL} ${DEBUG_TARBALL_URL} ${CHECKSUM_URL}"


# need to download?
for file in $FILE_NAMES; do
    fpath="${MCP_TARBALLS_DIR}/${file}"
    if [ -f "${fpath}" ]; then
        echo "File ${fpath} already exists; no need to download again."
        exit 0
    fi
done


# wget settings
WGET="wget"
WGETOPTS="--no-check-certificate --user=$PKVM_GSA_USER --password=$PKVM_GSA_PASS"


pushd $MCP_TARBALLS_DIR


# download files
for file in $FILE_URLS; do
    $WGET $WGETOPTS $file
done


# verify checksum
sha1sum -c $CHECKSUM_NAME || :


# create symlinks
ln -sf $RPMS_TARBALL_NAME $SYMLINK_NAME
ln -sf $DEBUG_TARBALL_NAME ${SYMLINK_NAME}-debuginfo


popd


exit 0
