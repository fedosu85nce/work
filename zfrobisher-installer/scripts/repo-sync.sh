#! /bin/sh


# use signed packages
TARBALL_SUFFIX=""
if [ "$USE_SIGNED_PACKAGES" = "true" ]; then
    TARBALL_SUFFIX="-signed"
fi


# settings
TEMPDIR=$(mktemp -d)


MCP_TARBALL_LINK="${MCP_TARBALLS_DIR}/${VENDOR}/${STREAM_VERSION}/${MCP_TARBALL_NAME}${TARBALL_SUFFIX}"
if ! test -L "$MCP_TARBALL_LINK"; then
    echo "ERROR No such file: $MCP_TARBALL_LINK" >&2
    exit 255
fi


MCP_TARBALL_PATH="${MCP_TARBALLS_DIR}/${VENDOR}/${STREAM_VERSION}/$(readlink $MCP_TARBALL_LINK)"
if ! test -f "$MCP_TARBALL_PATH"; then
    echo "ERROR No such file: $MCP_TARBALL_PATH" >&2
    exit 255
fi


echo "Using tarball file: $MCP_TARBALL_PATH"


# extract tarball
tar xvf $MCP_TARBALL_PATH -C $TEMPDIR


# exclude packages from repodata
ARGS=
if test -n "$EXCLUDE_MCP_PKGS"; then
    for VALUE in $EXCLUDE_MCP_PKGS; do
        ARGS="$ARGS -x $VALUE"
    done
fi


# delete mcp packages
if test -n "$DELETE_MCP_PKGS"; then
    for PKG in $DELETE_MCP_PKGS; do
        for FILE in $TEMPDIR/$PKG; do
            if test -f "$FILE"; then
                rm -fv "$FILE"
            fi
        done
    done
fi


# create mcp repodata
createrepo -v $ARGS $TEMPDIR


# create repo dir
REPO_DIR="${REPOS_DIR}/${VENDOR}/${STREAM_VERSION}/mcp"
rm -rf "$REPO_DIR"
mkdir -pv "$REPO_DIR"


# move content to the repo dir
mv $TEMPDIR/* $REPO_DIR


# identify which tarball was used to create the current mcp repo
cp -v $MCP_TARBALL_PATH.info $REPO_DIR/info
chmod 0644 $REPO_DIR/info


# cleanup
rm -rf $TEMPDIR


exit 0
