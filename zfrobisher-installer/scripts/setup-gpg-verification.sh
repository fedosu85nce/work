#!/usr/bin/env sh

# Do not verify GPG if building and internal image.

if [ "$RPM_GPG_VERIFY" = "false" ]; then
    touch "${ROOTFS_DIR}/etc/.dont_verify_gpg"
fi
