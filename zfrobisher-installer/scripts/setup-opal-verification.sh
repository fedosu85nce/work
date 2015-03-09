#! /bin/sh

# Do not verify OPAL if building an internal ISO image.

if [ "$EXTERNAL_BUILD" = "false" ]; then
    touch "${ROOTFS_DIR}/etc/.dont_verify_opal"
fi
