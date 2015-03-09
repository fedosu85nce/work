%define pkvm_version 2.1.0.2
%define pkvm_release 31
%define pkvm_respin .0

Name:           ibm-powerkvm-layer
Version:        %{pkvm_version}
Release:        %{pkvm_release}%{?pkvm_respin}%{?dist}
Summary:        IBM PowerKVM Layer
Group:          System Environment/Base
License:        EPL 
URL:            http://www.ibm.com
Source0:        README.txt
Source1:        README_base.txt
Requires:       ibm-powerkvm-layer-base

%description
IBM PowerKVM Layer

%package base
Summary:        IBM PowerKVM Layer Base
Requires:       ibm-powerkvm-config
Requires:       powerkvm-installer
Requires:       pkvm2_1-release

%description base
IBM PowerKVM Layer Base

%prep
%{__cp} %{SOURCE0} %{_builddir}
%{__cp} %{SOURCE1} %{_builddir}

%build

%install
%{__rm} -rf %{buildroot}
%{__mkdir_p} %{buildroot}

%files
%doc README.txt

%files base
%doc README_base.txt

%changelog
* Mon Apr 21 2014 User <user@domain> - 2.1.0-1
- Initial version
