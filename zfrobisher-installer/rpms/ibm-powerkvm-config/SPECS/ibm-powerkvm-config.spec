%define pkvm_version 2.1.0.2
%define pkvm_release 31
%define pkvm_respin .0

Name:           ibm-powerkvm-config
Version:        %{pkvm_version}
Release:        %{pkvm_release}%{?pkvm_respin}%{?dist}
Summary:        IBM PowerKVM Configuration
Group:          System Environment/Base
License:        EPL 
URL:            http://www.ibm.com
Source0:        README.txt
Source1001:     89-hw_random.rules

%description
IBM PowerKVM Configuration

%prep
%{__cp} %{SOURCE0} %{_builddir}
%{__cp} %{SOURCE1001} %{_builddir}

%build

%install
%{__rm} -rf %{buildroot}
%{__mkdir_p} %{buildroot}%{_sysconfdir}/udev/rules.d
%{__install} %{SOURCE1001} %{buildroot}%{_sysconfdir}/udev/rules.d

%files
%defattr(0644,root,root,-)
%{_sysconfdir}/udev/rules.d/89-hw_random.rules
%doc README.txt

%changelog
* Mon Apr 21 2014 User <user@domain> - 2.1.0-1
- Initial version
