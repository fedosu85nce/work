# ----
# zKVM installer spec file
# ----
%define zkvm_version 1.1.0
%define zkvm_release beta6.1

Name:      zkvm-installer
Version:   %{zkvm_version}
Release:   %{zkvm_release}%{?dist}
License:   EPL
Vendor:    IBM
Packager:  LTC
Group:     Application
Summary:   %{label} installer
Source:    zkvm.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}
Requires:  newt-python, python-pycurl, rpm-python

%description
%{label} installer tool

# Use MD5 for file digest (backwards compatible)
%global _binary_filedigest_algorithm 1
%global _source_filedigest_algorithm 1

# use gzip compression level 9
%global _binary_payload w9.gzdio
%global _source_payload w9.gzdio

%prep
%setup -n %{name}

%install
cp -a ./ %{buildroot}
find %{buildroot} -name .gitignore -exec rm {} \;

ln -s /usr/bin/ibm-configure-system %{buildroot}/usr/bin/configure-system

%post
# Do not print LVM warning in output - breaks newt screen
echo "export LVM_SUPPRESS_FD_WARNINGS=1" >> /etc/profile
# Do no print Kernel stuff in output - breaks newt screen
echo "kernel.printk = 3 4 1 3" >> /etc/sysctl.conf


%clean

%files
%defattr(-,root,root)
/opt/ibm/zkvm-installer/*
%dir /opt/ibm/zkvm-installer
%config %{_sysconfdir}/fstab
%config %{_sysconfdir}/multipath.conf
%config %{_sysconfdir}/sysconfig/network
/usr/bin/zkvm-installer
/usr/bin/ibm-configure-system
/usr/bin/ibm-update-system
/usr/bin/configure-system
/usr/sbin/zkvm
/lib/systemd/system/zkvm-direct.service
/lib/systemd/system/zkvm-sshd.service
/lib/systemd/system/zkvm.target
