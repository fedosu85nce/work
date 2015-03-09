#!/bin/sh


# gsa url
PKVM_UPDATES_GSA_URL="${PKVM_UPDATES_GSA_URL}/test"


# wget options
WGET="wget --no-check-certificate --user=$PKVM_GSA_USER --password=$PKVM_GSA_PASS"


# tarball with the powerkvm unsigned rpms
PKVM_UNSIGNED_TARBALL="powerkvm-rpms-unsigned-${BUILD_ID}.tar.gz"


# temp dir housing the rpms to be uploaded
RPMS_TEMP_DIR=$(mktemp -d)


# temp dir
TEMP_DIR=$(mktemp -d)


# create artifacts dir
ARTIFACTS_DIR="$WORKSPACE/artifacts"
[ ! -d $ARTIFACTS_DIR ] && mkdir -pv $ARTIFACTS_DIR


# create a repo with only powerkvm rpms
find ${RPMS_BASE_DIR}/${VENDOR}/${STREAM_VERSION} -type f -name "*.rpm" \
    | xargs -I% cp % $RPMS_TEMP_DIR


# add 3rd party rpms
if [[ -n $EXTERNAL_PACKAGES ]]; then
    pushd $RPMS_TEMP_DIR
    for url in $EXTERNAL_PACKAGES; do
        curl $url -O "$(basename $url)"
    done
    popd
fi


# generate a tarball with the rpms
pushd $RPMS_TEMP_DIR
tar czf $ARTIFACTS_DIR/${PKVM_UNSIGNED_TARBALL} *
popd


# generate a checksum file for the tarball
pushd $ARTIFACTS_DIR
for f in *; do
    sha1sum $f > ${f}.sha1sum
done
popd


# form STREAM_VERSION2 according to STREAM_VERSION specified as a parameter for this job
case ${STREAM_VERSION} in
    '2.1.0')
        STREAM_VERSION2="2_1"
        ;;
    '2.1.1')
        STREAM_VERSION2="2_1_1"
        ;;
    *)
        echo "ERROR: invalid value for STREAM_VERSION"
        exit 255
        ;;
esac


# form tarball prefix by replacing STREAM_VERSION by $STREAM_VERSION2
MCP_TARBALL_PREFIX="${MCP_TARBALL_PREFIX/STREAM_VERSION/$STREAM_VERSION2}"


# form the mcp build to match the same one in the mcp gsa url
YEAR="${MCP_BUILD_ID:0:4}"
MONTH="${MCP_BUILD_ID:4:2}"
DAY="${MCP_BUILD_ID:6:2}"
TIME="${MCP_BUILD_ID:9:6}"
MCP_BUILD_ID2="$YEAR-$MONTH-$DAY-$TIME"


# debug
echo year: $YEAR
echo month: $MONTH
echo day: $DAY
echo time: $TIME
echo build id1: $MCP_BUILD_ID
echo build id2: $MCP_BUILD_ID2


# set variable values
MCP_TARBALL="$MCP_TARBALL_PREFIX-${MCP_BUILD_ID2}-rpms.tar.gz"

MCP_TARBALL_DEBUG="$MCP_TARBALL_PREFIX-${MCP_BUILD_ID2}-debuginfo_rpms.tar.gz"
MCP_CHECKSUM="$MCP_TARBALL_PREFIX-${MCP_BUILD_ID2}-sha1sums.txt"

MCP_TARBALL_URL="${MCP_TARBALLS_URL}/${MCP_BUILD_ID}/$MCP_TARBALL_PREFIX-${MCP_BUILD_ID2}-rpms.tar.gz"
MCP_TARBALL_DEBUG_URL="${MCP_TARBALLS_URL}/${MCP_BUILD_ID}/${MCP_TARBALL_DEBUG}"
MCP_CHECKSUM_URL="${MCP_TARBALLS_URL}/${MCP_BUILD_ID}/${MCP_CHECKSUM}"


# download mcp checksum file
$WGET $MCP_CHECKSUM_URL -O $TEMP_DIR/$MCP_CHECKSUM


# set checksum variables
MCP_TARBALL_CHECKSUM=$(grep $MCP_TARBALL $TEMP_DIR/$MCP_CHECKSUM | cut -d" " -f1)
MCP_TARBALL_DEBUG_CHECKSUM=$(grep $MCP_TARBALL_DEBUG $TEMP_DIR/$MCP_CHECKSUM | cut -d" " -f1)
pushd $ARTIFACTS_DIR
PKVM_CHECKSUM=$(sha1sum $PKVM_UNSIGNED_TARBALL | cut -d" " -f1)
popd


# variables to be consumed by signer script
cat <<EOF > $ARTIFACTS_DIR/latest
LATEST_UNSIGNED_ID="$BUILD_ID"
LATEST_UNSIGNED_RUN="$(date)"

LATEST_UNSIGNED_MCP_BUILD_ID="$MCP_BUILD_ID"
LATEST_UNSIGNED_MCP_TARBALL_NAME="$MCP_BUILD_NAME"

LATEST_UNSIGNED_MCP_TARBALL="$MCP_TARBALL"
LATEST_UNSIGNED_MCP_TARBALL_CHECKSUM="$MCP_TARBALL_CHECKSUM"
LATEST_UNSIGNED_MCP_TARBALL_URL="$MCP_TARBALL_URL"

LATEST_UNSIGNED_MCP_TARBALL_DEBUG="$MCP_TARBALL_DEBUG"
LATEST_UNSIGNED_MCP_TARBALL_DEBUG_CHECKSUM="$MCP_TARBALL_DEBUG_CHECKSUM"
LATEST_UNSIGNED_MCP_TARBALL_DEBUG_URL="$MCP_TARBALL_DEBUG_URL"

LATEST_UNSIGNED_PKVM_TARBALL="$PKVM_UNSIGNED_TARBALL"
LATEST_UNSIGNED_PKVM_TARBALL_CHECKSUM="$PKVM_CHECKSUM"
LATEST_UNSIGNED_PKVM_TARBALL_URL="${PKVM_UPDATES_GSA_URL}/unsigned/${VENDOR}/${STREAM_VERSION}/${BUILD_ID}/$PKVM_UNSIGNED_TARBALL"

EXCLUDE_MCP_PKGS="$EXCLUDE_MCP_PKGS"
DELETE_MCP_PKGS="$DELETE_MCP_PKGS"

SIGN_DEBUGINFO="$SIGN_DEBUGINFO"

STREAM_VERSION="$STREAM_VERSION"
VENDOR="$VENDOR"
EOF
cat $ARTIFACTS_DIR/latest


# cleanup
rm -rf $RPMS_TEMP_DIR
rm -rf $TEMP_DIR
