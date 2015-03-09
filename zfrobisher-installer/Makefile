include Makefile.config

all: \
	config \
	create_initrd \
	i18n \
	create_repo_frobisher \
	customize_rootfs_image \
	create_rootfs_image \
	pack \
	tag_iso \
	make_iso \
	finish

#----------------------------------------------------------------------
# Initializes the build system
#----------------------------------------------------------------------
config:
	@./scripts/osd.py TITLE Preparing build environment

	# create base directories
	mkdir -p $(KOP_RELEASE)
	mkdir -p $(BUILD_DIR)/{ext,package}
	mkdir -p $(BUILD_DIR)/sqsh/LiveOS
	mkdir -p $(ROOTFS_DIR)
	mkdir -p $(RPM_DIR)/rpmbuild/{SPECS,SOURCES,SRPMS,RPMS,BUILD,BUILDROOT}
	mkdir -p $(DVD_DIR)/{etc,LiveOS,ppc/{chrp,ppc64},packages}

	# setup the dvd directory
	cp -r $(OVERLAY_DIR)/dvd/* $(DVD_DIR)

	# extract export-root to build dir
	tar -zxvf ./export-root/*.tar.gz -C $(ROOTFS_DIR) > /dev/null

#----------------------------------------------------------------------
# Creates the initrd
#----------------------------------------------------------------------
create_initrd:
	@./scripts/osd.py TITLE Creating initrd

	# setup dracut config file
	cp -r $(OVERLAY_DIR)/initrd/* $(ROOTFS_DIR)/

	# mount system dirs
	mount --bind /proc $(ROOTFS_DIR)/proc
	mount --bind /sys $(ROOTFS_DIR)/sys
	mount --bind /dev $(ROOTFS_DIR)/dev
	mount --bind /run $(ROOTFS_DIR)/run
	mount -t devpts -o gid=5,mode=620 devpts $(ROOTFS_DIR)/dev/pts
	mount -t tmpfs -o defaults tmpfs $(ROOTFS_DIR)/dev/shm
	mount -t selinuxfs -o defaults selinuxfs $(ROOTFS_DIR)/sys/fs/selinux

	time chroot $(ROOTFS_DIR) restorecon -R -F /

	# generate the initrd
	sed -i "s@multipath_component_detection = 1@multipath_component_detection = 0@"  $(ROOTFS_DIR)/etc/lvm/lvm.conf
	chroot $(ROOTFS_DIR) mpathconf --enable --with_multipathd y
	chroot $(ROOTFS_DIR) dracut /tmp/initrd.img $(shell chroot $(ROOTFS_DIR) ls /lib/modules/)

	time chroot $(ROOTFS_DIR) restorecon -R -F /

	# umount system dirs
	umount $(ROOTFS_DIR)/dev/pts
	umount $(ROOTFS_DIR)/dev/shm
	umount $(ROOTFS_DIR)/sys/fs/selinux
	umount $(ROOTFS_DIR)/run
	umount $(ROOTFS_DIR)/dev
	umount $(ROOTFS_DIR)/sys
	umount $(ROOTFS_DIR)/proc

	# move the initrd to dvd boot
	mv $(ROOTFS_DIR)/tmp/initrd.img $(DVD_DIR)/ppc/ppc64/

#----------------------------------------------------------------------
# Creates i18n
#----------------------------------------------------------------------
i18n:
	@./scripts/osd.py TITLE Generating i18n files
	@./scripts/generate_mo_files.sh

#----------------------------------------------------------------------
# Apply Copyright to source files
#----------------------------------------------------------------------
apply_copyright:
	@./scripts/osd.py TITLE Applying copyright
	@./scripts/apply-copyright.sh

#----------------------------------------------------------------------
# Generate rpms
#----------------------------------------------------------------------
rpm: i18n
	./scripts/osd.py TITLE Generating RPMs
	./scripts/generate-rpms.sh

customize_rootfs_image: rpm
	./scripts/osd.py TITLE Customizing RootFS Image
	./scripts/customize-rootfs-image.sh

#----------------------------------------------------------------------
# Creates the ROOTFS (squashed)
#----------------------------------------------------------------------
create_rootfs_image:
	@./scripts/osd.py TITLE Creating Squashed RootFS Ext3 Image

	# create a ext3 image
	./scripts/create_rootfs_image.sh $(BUILD_DIR) $(ROOTFS_DIR) $(DVD_DIR)

#----------------------------------------------------------------------
# Create local repository
#----------------------------------------------------------------------
create_local_repo:
	./scripts/osd.py TITLE Creating Local Repository
	./scripts/local-repo.sh

#----------------------------------------------------------------------
# Creates the repository (frobisher)
#----------------------------------------------------------------------
create_repo_frobisher:
	@./scripts/osd.py TITLE Creating Frobisher Repository

	# copy packages to dvd
	cp -rf $(REPO_DIR)/* $(DVD_DIR)/packages
	createrepo -v $(DVD_DIR)/packages

	for PKG in $(DVD_DIR)/packages/*.rpm; do \
		rpm -qp $$PKG >> $(KOP_RELEASE)/production_packages.list; \
		rpm -qp --qf "%{SOURCERPM}  %{EPOCH}:%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n" $$PKG >> $(KOP_RELEASE)/production_packages_sources.list; \
	done
	sort $(KOP_RELEASE)/production_packages.list > $(KOP_RELEASE)/production_packages.list.sorted
	sort $(KOP_RELEASE)/production_packages_sources.list > $(KOP_RELEASE)/production_packages_sources.list.sorted
	mv -v $(KOP_RELEASE)/production_packages.list{.sorted,}
	mv -v $(KOP_RELEASE)/production_packages_sources.list{.sorted,}

#----------------------------------------------------------------------
# Creates the netboot deliverable
#----------------------------------------------------------------------
pack:
	@./scripts/osd.py TITLE Packaging the NETBOOT version
	./scripts/pack-netboot-tarball.sh

#----------------------------------------------------------------------
# Tag ISO
#----------------------------------------------------------------------
tag_iso:
	@./scripts/osd.py TITLE Tagging ISO

	# create VERSION
	echo "BUILD_NAME=$(BUILD_NAME)" >> $(DVD_DIR)/VERSION
	echo "BUILD_NUMBER=$(BUILD_NUMBER)" >> $(DVD_DIR)/VERSION
	echo "BASE_BUILD=$(BUILD_ID)" >> $(DVD_DIR)/VERSION

	# create .discinfo
	./scripts/makestamp.py --releasestr="$(DISCINFO_STR)" --arch="ppc64" --outfile=$(DVD_DIR)/.discinfo

#----------------------------------------------------------------------
# Creates the ISO
#----------------------------------------------------------------------
make_iso:
	@./scripts/osd.py TITLE Creating ISO

	# create iso
	mkisofs -v -r -T -U -l -cache-inodes -chrp-boot -V POWERKVM_LIVECD -o \
		$(KOP_RELEASE)/ibm-powerkvm-$(ISO_VERSION)-$(ISO_BUILD)-ppc64-$(ISO_MILESTONE)-$(TIMESTAMP).iso \
		$(BUILD_DIR)/dvd > /dev/null

#----------------------------------------------------------------------
# Cleanup the mess and finishes
#----------------------------------------------------------------------
finish:
	@./scripts/osd.py TITLE Finishing Build

	rm -fr $(BUILD_DIR)
	pushd $(KOP_RELEASE); md5sum ibm-powerkvm-* > MD5SUM
	./scripts/osd.py TITLE Deliverables At $(KOP_RELEASE)

#----------------------------------------------------------------------
# Clean tmp
#----------------------------------------------------------------------
clean:
	find . -type d -exec umount '{}' \; > /dev/null 2>&1
	rm -fr ./releases/*

#----------------------------------------------------------------------
# Repo Diff
#----------------------------------------------------------------------
repo-diff:
	@./scripts/osd.py TITLE Creating Repo Diff
	sh -x scripts/repo-diff.sh
