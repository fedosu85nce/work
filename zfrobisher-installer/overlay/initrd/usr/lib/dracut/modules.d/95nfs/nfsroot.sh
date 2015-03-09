#!/bin/sh
# -*- mode: shell-script; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# ex: ts=8 sw=4 sts=4 et filetype=sh

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
. /lib/nfs-lib.sh

[ "$#" = 3 ] || exit 1

# root is in the form root=nfs[4]:[server:]path[:options], either from
# cmdline or dhcp root-path
netif="$1"
root="$2"
NEWROOT="$3"

MOUNT_DIR="/tmp/nfsmp"
ISO_DIR="/tmp/isomp"

nfs_to_var $root $netif
[ -z "$server" ] && die "Required parameter 'server' is missing"

# get nfs path and iso
iso_name=${root##*/}
iso_name=${iso_name%:*}
nfs_path=${root%/*}

# create base directory
mkdir -p $MOUNT_DIR
mkdir -p $ISO_DIR

# mount NFS
info "Mounting NFS [$nfs_path]"
mount_nfs "$nfs_path" $MOUNT_DIR $netif

# iso not found: panic!
[ ! -f $MOUNT_DIR/$iso_name ] && die "$iso_name not found in the NFS path."

# copy files locally
info "Copying ISO locally..."
cp $MOUNT_DIR/$iso_name /tmp

# umount everything
umount /tmp/nfsmp

# mount the ISO
mount -o loop /tmp/$iso_name $ISO_DIR

# create the rw loop and mount in new root
info "Mounting rootfs..."
/sbin/dmsquash-live-root $ISO_DIR/LiveOS/squashfs.img
mount /dev/mapper/live-rw "$NEWROOT"
[ "$?" != "0" ] && die "Panic: cannot mount rootfs"

# copy the repository into the new root
mkdir -p "$NEWROOT"/var/kop
cp -a $ISO_DIR/packages/* "$NEWROOT"/var/kop

info "rootfs mounted successfuly. Finishing the init process."

exit 0
