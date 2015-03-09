#!/bin/bash

#----------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------

readonly BUILD_DIR="$1"
readonly ROOTFS_DIR="$2"
readonly DVD_DIR="$3"

# format command
readonly MKFS="mkfs.ext3"

# image name
readonly EXT_IMG="ext3fs.img"

# image size - 2GB
# TODO: find image size dynamically based on rootfs size
readonly IMG_SIZE=2000

#----------------------------------------------------------------------
# Code
#----------------------------------------------------------------------

# createExtImage
#
# Creates an ext image and copy the rootfs inside it
#
# rtype:   nothing
# returns: nothing
function createExtImage()
{
    # create and format an ext image
    dd if=/dev/zero of="$BUILD_DIR/$EXT_IMG" bs=1M count=$IMG_SIZE > /dev/null 2>&1
    yes | $MKFS "$BUILD_DIR/$EXT_IMG" > /dev/null 2>&1

    # mount the image
    mount -o loop "$BUILD_DIR/$EXT_IMG" "$BUILD_DIR/ext"

    # copy the rootfs to the ext image
    cp -a "$ROOTFS_DIR"/* "$BUILD_DIR/ext"

    # remove root password and restore selinux policy
    chroot "$BUILD_DIR/ext" passwd -d root

    mount -o bind /proc "$BUILD_DIR/ext/proc" 
    mount -o bind /dev "$BUILD_DIR/ext/dev" 
    mount -o bind /sys "$BUILD_DIR/ext/sys" 
    mount -o bind /run "$BUILD_DIR/ext/run" 
    mount -t devpts -o gid=5,mode=620 devpts "$BUILD_DIR/ext/dev/pts"
    mount -t tmpfs -o defaults tmpfs "$BUILD_DIR/ext/dev/shm"
    mount -t selinuxfs -o defaults selinuxfs "$BUILD_DIR/ext/sys/fs/selinux"

    time chroot "$BUILD_DIR/ext" restorecon -R -F /

    umount "$BUILD_DIR/ext/sys/fs/selinux"
    umount "$BUILD_DIR/ext/dev/shm"
    umount "$BUILD_DIR/ext/dev/pts"
    umount "$BUILD_DIR/ext/run"
    umount "$BUILD_DIR/ext/sys"
    umount "$BUILD_DIR/ext/dev"
    umount "$BUILD_DIR/ext/proc"

    # unmount the image
    umount "$BUILD_DIR/ext"
}

# createSquashFS
#
# Creates a squashfs image based on the ext
#
# rtype:   nothing
# returns: nothing
function createSquashFS()
{
    # copy the ext image to a LiveOS dir (required by dracut)
    cp "$BUILD_DIR/$EXT_IMG" "$BUILD_DIR/sqsh/LiveOS/"

    # generate the squashfs image
    mksquashfs "$BUILD_DIR/sqsh/" "$BUILD_DIR/squashfs.img"

    # copy the squashfs to the DVD dir
    cp "$BUILD_DIR/squashfs.img" "$DVD_DIR/LiveOS"
}

# main
#
# Entry point
#
# rtype:   nothing
# returns: nothing
function main()
{
    createExtImage
    createSquashFS
}

main
