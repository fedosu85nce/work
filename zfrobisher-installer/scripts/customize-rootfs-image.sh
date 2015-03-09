#! /bin/sh

# copy kernel to DVD
cp $ROOTFS_DIR/boot/vmlinuz-$(chroot $ROOTFS_DIR ls /lib/modules/) $DVD_DIR/ppc/ppc64/vmlinuz

# update yaboot label to reflect KVM On Power name
find $DVD_DIR/etc -name yaboot.conf -exec sed -i s@KOPLABEL@$KOP_LABEL@ {} \;

# enable selinux in dvd
sed -i 's/^SELINUX=.*/SELINUX=permissive/g' $ROOTFS_DIR/etc/selinux/config

# Permit root ssh without password in the LiveDVD
echo "PermitEmptyPasswords yes" >> $ROOTFS_DIR/etc/ssh/sshd_config

# IBM Power systems pick /etc/yaboot.conf for yaboot.  Apple
# Power systems pick /ppc/ppc{32,64}/yaboot.conf for yaboot.
# For more details, see https://git.fedorahosted.org/cgit/lorax.git/tree/share/ppc.tmpl?h=f19-branch#n29
cp -fv $DVD_DIR/etc/yaboot.conf $DVD_DIR/ppc/ppc64/yaboot.conf

# For the development build, we need to generate a new
# powerkvm-installer rpm with the latest source code.
if [ "$EXTERNAL_BUILD" = "false" -o "$RPM_GPG_VERIFY" = "false" ]; then
    # copy powerkvm-installer rpm to rootfs
    for pkg in rpms/powerkvm-installer/RPMS/noarch/powerkvm-installer*rpm; do
        cp -v $pkg $ROOTFS_DIR/tmp
    done

    # install powerkvm-installer rpm on rootfs
    chroot $ROOTFS_DIR rpm -Uvh --force --allfiles /tmp/*.rpm

    # cleanup rootfs
    rm -fv $ROOTFS_DIR/tmp/*.rpm
fi

# generate a list of installed packages in rootfs
chroot $ROOTFS_DIR rpm -qa | sort > $KOP_RELEASE/rootfs_packages.list
chroot $ROOTFS_DIR rpm -qa --qf "%{SOURCERPM}  %{EPOCH}:%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n" | sort > $KOP_RELEASE/rootfs_packages_sources.list

# setup fstab
cp $OVERLAY_DIR/powerkvm-installer/etc/fstab $ROOTFS_DIR/etc

# tmux config
cp $OVERLAY_DIR/rootfs/etc/tmux-pkvm.conf $ROOTFS_DIR/etc

# setup OPAL verification
sh -x ./scripts/setup-opal-verification.sh

# setup GPG verification
sh -x ./scripts/setup-gpg-verification.sh

# autologin
# serial terminal (hvc0)
cp $ROOTFS_DIR/usr/lib/systemd/system/serial-getty@.service $ROOTFS_DIR/etc/systemd/system/serial-getty@hvc0.service
sed -i 's:ExecStart=-.*:ExecStart=-/sbin/agetty --autologin root -s %I 115200,38400,9600 xterm:' $ROOTFS_DIR/etc/systemd/system/serial-getty@hvc0.service
#ln -sf /etc/systemd/system/serial-getty@hvc0.service $ROOTFS_DIR/etc/systemd/system/getty.target.wants/
# virtual terminal (tty1)
cp $ROOTFS_DIR/usr/lib/systemd/system/getty@.service $ROOTFS_DIR/etc/systemd/system/getty@tty1.service
sed -i 's:ExecStart=-.*:ExecStart=-/sbin/agetty --autologin root %I 38400 linux:' $ROOTFS_DIR/etc/systemd/system/getty@tty1.service
#ln -sf /etc/systemd/system/getty@tty1.service $ROOTFS_DIR/etc/systemd/system/getty.target.wants/
# virtual terminal (tty2)
cp $ROOTFS_DIR/usr/lib/systemd/system/getty@.service $ROOTFS_DIR/etc/systemd/system/getty@tty2.service
sed -i 's:ExecStart=-.*:ExecStart=-/sbin/agetty --autologin root %I 38400 linux:' $ROOTFS_DIR/etc/systemd/system/getty@tty2.service
# autostart
cp $OVERLAY_DIR/rootfs/root/.bash_profile $ROOTFS_DIR/root/.bash_profile

sha1sum $DVD_DIR/packages/repodata/*-primary.sqlite.bz2 > $ROOTFS_DIR/primary-livecd.sha1
