#!/bin/sh


function do_debuginfo() {
    if test "$DOWNLOAD_DEBUGINFO" = "true"; then
        return 0
    fi
    return 1
}


# directory where downloaded tarballs should be placed
TARBALLS_DIR=$TARBALLS_BASE_DIR/$VENDOR/$STREAM_VERSION
if ! test -d "$TARBALLS_DIR"; then
    mkdir -pv "$TARBALLS_DIR"
fi


# where signed tarballs will be downloaded
TEMP_DIR=$(mktemp -d)


# content of /signed/latest from gsa
LATEST_SIGNED_METADATA_FILE=$(mktemp)
LATEST_SIGNED_CONFIG_FILE=$(mktemp)


# wget options
WGET="wget --no-check-certificate --user=$PKVM_GSA_USER --password=$PKVM_GSA_PASS"


# download latest signed metadata
$WGET $PKVM_UPDATES_GSA_URL/test/signed/latest -O $LATEST_SIGNED_METADATA_FILE
source $LATEST_SIGNED_METADATA_FILE


# if user specified SIGNED_BUILD_ID in the Jenkins recipe,
# override LATEST_SIGNED_ID
if [ -n "$SIGNED_BUILD_ID" ]; then
    LATEST_SIGNED_ID=$SIGNED_BUILD_ID
fi


# download config file for the latest signed build
$WGET $PKVM_UPDATES_GSA_URL/test/signed/$LATEST_SIGNED_VENDOR/$LATEST_SIGNED_STREAM_VERSION/$LATEST_SIGNED_ID/config -O $LATEST_SIGNED_CONFIG_FILE
source $LATEST_SIGNED_CONFIG_FILE


# download signed tarballs
FILES_TO_DOWNLOAD="$SIGNED_PKVM_TARBALL"
if do_debuginfo; then
    FILES_TO_DOWNLOAD="$FILES_TO_DOWNLOAD $SIGNED_MCP_TARBALL_DEBUG"
fi
for f in $FILES_TO_DOWNLOAD; do
    URL="$PKVM_UPDATES_GSA_URL/test/signed/$SIGNED_VENDOR/$SIGNED_STREAM_VERSION/$LATEST_SIGNED_ID/$f"
    OUTFILE="$TEMP_DIR/$f"
    $WGET $URL -O $OUTFILE
done


# create checksum files
echo "$SIGNED_PKVM_TARBALL_CHECKSUM  $SIGNED_PKVM_TARBALL" > $TEMP_DIR/$SIGNED_PKVM_TARBALL.sha1sum
if do_debuginfo; then
    echo "$SIGNED_MCP_TARBALL_DEBUG_CHECKSUM  $SIGNED_MCP_TARBALL_DEBUG" > $TEMP_DIR/$SIGNED_MCP_TARBALL_DEBUG.sha1sum
fi


# verify checksums
pushd $TEMP_DIR
for f in *.sha1sum; do
    sha1sum -c $f
done
popd


# move signed tarballs to the tarballs directory
mv -v $TEMP_DIR/* $TARBALLS_DIR


# create symlinks
pushd $TARBALLS_DIR
ln -sf $SIGNED_PKVM_TARBALL $MCP_BUILD_NAME-signed
if do_debuginfo; then
    ln -sf $SIGNED_MCP_TARBALL_DEBUG $MCP_BUILD_NAME-debuginfo-signed
fi
popd


# create .info file containing all the information of the signed tarballs
cp $LATEST_SIGNED_CONFIG_FILE $TARBALLS_DIR/$SIGNED_PKVM_TARBALL.info


# debug
ls -al $TEMP_DIR


# cleanup
rm -rf $TEMP_DIR
rm -rf $LATEST_SIGNED_METADATA_FILE
rm -rf $LATEST_SIGNED_CONFIG_FILE


exit 0
