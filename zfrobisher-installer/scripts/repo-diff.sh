#! /bin/sh


function setup_lftprc() {
    sed -e "s,@GSA_HOST@,$GSA_HOST,g" \
        -e "s,@GSA_USER@,$GSA_USER,g" \
        -e "s,@GSA_PASS@,$GSA_PASS,g" \
        -e "s,@GSA_DIR@,$GSA_DIR,g" \
        $LFTPRC_TEMPLATE > $LFTPRC
}


function do_debuginfo() {
    if test "$CREATE_DEBUGINFO" = "true"; then
        return 0
    fi
    return 1
}


function do_tarballs() {
    if test "$CREATE_TARBALLS" = "true"; then
        return 0
    fi
    return 1
}


function upload_iso() {
    if test "$UPLOAD_ISO" != "true"; then
        echo "Skipping the upload of ISOs"
        return 1
    fi

    echo "Creating remote directory: ${ISOS_RDIR}"
    ./scripts/lftp.sh mkdir -p ${ISOS_RDIR}

    echo "Uploading ISO: ${UPDATE_ISO_NAME}"
    ./scripts/lftp.sh put -c ${FINAL_UPDATE_ISO} -o ${ISOS_RDIR}/${UPDATE_ISO_NAME}
    ./scripts/lftp.sh put -c ${FINAL_UPDATE_ISO}.sha1sum -o ${ISOS_RDIR}/${UPDATE_ISO_NAME}.sha1sum

    if do_debuginfo; then
        echo "Uploading ISO debuginfo: ${DEBUG_ISO_NAME}"
        ./scripts/lftp.sh put -c ${FINAL_UPDATE_ISO_DEBUG} -o ${ISOS_RDIR}/${DEBUG_ISO_NAME}
        ./scripts/lftp.sh put -c ${FINAL_UPDATE_ISO_DEBUG}.sha1sum -o ${ISOS_RDIR}/${DEBUG_ISO_NAME}.sha1sum
    fi
}


function upload_packages() {
    if test "$UPLOAD_PACKAGES" != "true"; then
        echo "Skipping the upload of packages"
        return 1
    fi

    # updates
    echo "Creating remote directory: ${UPDATES_RDIR}"
    ./scripts/lftp.sh rm -r ${UPDATES_RDIR}
    ./scripts/lftp.sh mkdir -p ${UPDATES_RDIR}

    echo "Mirroring ${UPDATE_REPO_DIR} to ${UPDATES_RDIR}"
    ./scripts/lftp.sh mirror -R ${UPDATE_REPO_DIR} ${UPDATES_RDIR}

    # debuginfo
    if do_debuginfo; then

        echo "Creating remote directory: ${DEBUGINFO_RDIR}"
        ./scripts/lftp.sh rm -r ${DEBUGINFO_RDIR}
        ./scripts/lftp.sh mkdir -p ${DEBUGINFO_RDIR}

        echo "Mirroring ${DEBUG_REPO_DIR} to ${DEBUGINFO_RDIR}"
        ./scripts/lftp.sh mirror -R ${DEBUG_REPO_DIR} ${DEBUGINFO_RDIR}
    fi
}


# settings
PREFIX_NAME="ibm-powerkvm"
SUFFIX_NAME="${ISO_VERSION}-${ISO_BUILD}-ppc64-${ISO_MILESTONE}-${TIMESTAMP}"

ARTIFACTS_DIR="${WORKSPACE}/artifacts"

UPDATE_ISO_NAME="${PREFIX_NAME}-updates-${SUFFIX_NAME}.iso"
FINAL_UPDATE_ISO="${ARTIFACTS_DIR}/${UPDATE_ISO_NAME}"
DEBUG_ISO_NAME="${PREFIX_NAME}-debuginfo-${SUFFIX_NAME}.iso"
FINAL_UPDATE_ISO_DEBUG="${ARTIFACTS_DIR}/${DEBUG_ISO_NAME}"

FINAL_UPDATE_TARBALL="${ARTIFACTS_DIR}/${PREFIX_NAME}-${SUFFIX_NAME}.tar.gz"
FINAL_DEBUG_TARBALL="${ARTIFACTS_DIR}/${PREFIX_NAME}-debuginfo-${SUFFIX_NAME}.tar.gz"

BASE_TARBALL_DIR=$(mktemp -d)
UPDATE_TARBALL_DIR=$(mktemp -d)

DEBUG_ISO_DIR=$(mktemp -d)
DEBUG_REPO_DIR="${DEBUG_ISO_DIR}/packages"

ISO_DIR=$(mktemp -d)
UPDATE_REPO_DIR="${ISO_DIR}/packages"

export LFTPRC="scripts/lftprc"
LFTPRC_TEMPLATE="scripts/lftp.template"
GSA_DIR="${GSA_DIR}"
STAGING_RDIR="${GSA_DIR}/devel"
if test "$OFFICIAL_STAGING" = "true"; then
    STAGING_RDIR="${GSA_DIR}/staging"
fi
ISOS_RDIR="${STAGING_RDIR}/${VENDOR}/${STREAM_VERSION}/isos"
UPDATES_RDIR="${STAGING_RDIR}/${VENDOR}/${STREAM_VERSION}/updates"
DEBUGINFO_RDIR="${STAGING_RDIR}/${VENDOR}/${STREAM_VERSION}/debuginfo"
setup_lftprc

PKGSLIST_BASE="packages.list.base"
PKGSLIST_LATEST="packages.list.latest"


mkdir -pv "$UPDATE_REPO_DIR"
mkdir -pv "$DEBUG_REPO_DIR"


# clean dirty artifacts
rm -rfv "$ARTIFACTS_DIR"
mkdir -pv "$ARTIFACTS_DIR"


# tarball suffix
TARBALL_SUFFIX=
if test "$USE_SIGNED_PACKAGES" = "true"; then
    TARBALL_SUFFIX="-signed"
fi


# tarballs dir
TARBALLS_DIR="${TARBALLS_BASE_DIR}/${VENDOR}/${STREAM_VERSION}"


# extract base tarballs
tar xf "${TARBALLS_DIR}/${BASE_TARBALL}${TARBALL_SUFFIX}" \
    -C "$BASE_TARBALL_DIR"
if do_debuginfo; then
    tar xf "${TARBALLS_DIR}/${BASE_TARBALL_DEBUGINFO}${TARBALL_SUFFIX}" \
        -C "$DEBUG_REPO_DIR"
fi


# extract update tarballs
if [ -n "$UPDATE_TARBALLS" ]; then
    for tarball in $UPDATE_TARBALLS; do
        tar xf "${TARBALLS_DIR}/${tarball}${TARBALL_SUFFIX}" \
            -C "$UPDATE_TARBALL_DIR"
    done
fi


# extract update debuginfo tarballs
if do_debuginfo; then
    if [ -n "$UPDATE_TARBALLS_DEBUGINFO" ]; then
        for tarball in $UPDATE_TARBALLS_DEBUGINFO; do
            tar xf "${TARBALLS_DIR}/${tarball}${TARBALL_SUFFIX}" \
                -C "$DEBUG_REPO_DIR"
        done
    fi
fi


# checkout packages.list from $BASE_TAG and from HEAD
pushd $WORKSPACE
git show ${BASE_TAG}:packages.list > ${PKGSLIST_BASE}
git show HEAD:packages.list > ${PKGSLIST_LATEST}


# sort files
for file in ${PKGSLIST_BASE} ${PKGSLIST_LATEST}; do
    sort -u $file -o $file
done


# get a list of new packages that were added in packages.list
diff --text --left-column ${PKGSLIST_BASE} ${PKGSLIST_LATEST} \
    | grep ">" | sed -e 's,> ,,g' > new-pkgs-from-git


# obtain list of packages in each directory
for dir in $BASE_TARBALL_DIR $UPDATE_TARBALL_DIR; do
    pushd $dir
    ls -1 | sort -u > rpms
    popd
done


# File ${UPDATE_TARBALL_DIR}/rpms should also contain the rpms from
# the base tarball.  This is just for the sake of comparison when
# performing the diff between the list of rpms from each directory.
cat ${BASE_TARBALL_DIR}/rpms ${UPDATE_TARBALL_DIR}/rpms \
    > ${UPDATE_TARBALL_DIR}/rpms.tmp
sort -u ${UPDATE_TARBALL_DIR}/rpms.tmp > ${UPDATE_TARBALL_DIR}/rpms


# get a list of new packages since last build of PowerKVM
diff --text --left-column $BASE_TARBALL_DIR/rpms $UPDATE_TARBALL_DIR/rpms \
    | grep ">" | sed -e 's,> ,,g' > new-pkgs-from-tarball


# Remove from $UPDATE_TARBALL_DIR the list of packages equals to the
# list from $BASE_TARBALL_DIR and that is not in new-pkgs-from-git.
for package in $(< ${BASE_TARBALL_DIR}/rpms); do
    rpm_name=$(rpm -qp --qf="%{name}" ${UPDATE_TARBALL_DIR}/${package})
    if ! grep -qP "^${rpm_name}$" new-pkgs-from-git; then
        file="${UPDATE_TARBALL_DIR}/${package}"
        if [[ -f "${file}" ]]; then
            rm -fv "${file}"
        fi
    else
        echo "${package} is in new-pkgs-from-git (not removing)"
    fi
done


# Packages that go into the output directory.
FILTER_PKGS="filtered_pkgs.txt"


# Obtain just the name of rpms from new packages from tarball.
for line in $(< new-pkgs-from-tarball); do
    rpm -qp --qf="%{name}\n" ${UPDATE_TARBALL_DIR}/${line} \
        >> rpm-names-from-tarball
done


for rpm in ${UPDATE_TARBALL_DIR}/*.rpm; do

    rpm_name=$(rpm -qp --qf="%{name}" ${rpm})

    if grep -qP "^${rpm_name}$" packages.list; then
        # Here, the $rpm_name matched at least one line in
        # packages.list so the $rpm is a potential update.  Now, we
        # need to verify if $rpm_name is in the list of new packages
        # from git or from tarballs.  If it is in any of these two
        # lists, $rpm can be considered an update and can be copied to
        # the output directory.

        if grep -qP "^${rpm_name}$" new-pkgs-from-git; then
            echo "${rpm} is an update (matched new-pkgs-from-git)"
            echo ${rpm/${UPDATE_TARBALL_DIR}\/} >> ${FILTER_PKGS}
        fi

        if grep -qP "^${rpm_name}$" rpm-names-from-tarball; then
                echo "${rpm} is an update (matched new-pkgs-from-tarball)"
                echo ${rpm/${UPDATE_TARBALL_DIR}\/} >> ${FILTER_PKGS}
        fi
    fi
done


# debug purpose
echo "==>  New packages from git"
cat new-pkgs-from-git
echo "==>  New packages from tarballs"
cat new-pkgs-from-tarball
echo "==>  Packages udpated (ones that go into the output directory)"
cat ${FILTER_PKGS}


# pack updates
for package in $(paste -s -d" " ${FILTER_PKGS}); do
    for file in ${UPDATE_TARBALL_DIR}/${package}; do
        if [[ -f "$file" ]]; then
            mv -v "${file}" "${UPDATE_REPO_DIR}"
        fi
    done
done


# run createrepo on repos
createrepo -v $UPDATE_REPO_DIR
if do_debuginfo; then
    createrepo -v $DEBUG_REPO_DIR
fi


# pack tarballs
if do_tarballs; then

    # tarball with updates
    pushd $UPDATE_REPO_DIR
    tar czf $FINAL_UPDATE_TARBALL *
    popd

    # debuginfo tarball with updates
    if do_debuginfo; then
        pushd $DEBUG_REPO_DIR
        tar czf $FINAL_DEBUG_TARBALL *
        popd
    fi
fi


# create .discinfo in the root of the iso
./scripts/makestamp.py --releasestr="${DISCINFO_STR}" --arch="ppc64" \
                       --outfile="${ISO_DIR}/.discinfo"

./scripts/makestamp.py --releasestr="${DISCINFO_STR}" --arch="ppc64" \
                       --outfile="${DEBUG_ISO_DIR}/.discinfo"
sed -i'' -r -e 's,^(.*)(KVM\s)(.*)$,\1KVM d\3,g' "${DEBUG_ISO_DIR}/.discinfo"


# generate update iso
if [ "$GENERATE_UPDATE_ISO" = "true" ]; then
    mkisofs $MKISOFS_OPTS -V $PKVM_LIVECD_LABEL \
            -o "$FINAL_UPDATE_ISO" "$ISO_DIR"
fi


# debuginfo iso
if do_debuginfo; then
    mkisofs $MKISOFS_OPTS -V "${PKVM_LIVECD_LABEL}_DEBUGINFO" \
            -o "$FINAL_UPDATE_ISO_DEBUG" "$DEBUG_ISO_DIR"
fi


# checksums
pushd $ARTIFACTS_DIR
for f in *; do
    sha1sum $f > ${f}.sha1sum
done
popd


# upload to gsa
upload_iso
upload_packages


# clean up
rm -rf $BASE_TARBALL_DIR
rm -rf $UPDATE_TARBALL_DIR
rm -rf $ISO_DIR
rm -rf $DEBUG_ISO_DIR


exit 0
