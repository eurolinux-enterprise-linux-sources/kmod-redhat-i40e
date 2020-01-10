%define kmod_name		i40e
%define kmod_vendor		redhat
%define kmod_driver_version	2.1.14_k_dup7.4
%define kmod_rpm_release	2.1
%define kmod_kernel_version	3.10.0-693.el7
%define kmod_kbuild_dir		drivers/net/ethernet/intel/i40e
%define kmod_dependencies       %{nil}
%define kmod_build_dependencies	%{nil}
%define kmod_devel_package	0

%{!?dist: %define dist .el7_4}
%{!?make_build: %define make_build make}

Source0:	%{kmod_name}-%{kmod_vendor}-%{kmod_driver_version}.tar.bz2
# Source code patches
Patch0:	0000-introduce-backport-compat-header.patch
Patch1:	0001-add-gmb-macro.patch
Patch2:	0002-revert-netdrv-i40e-i40evf-adjust-packet-size-to-account-for.patch
Patch3:	0003-revert-intel-use-core-min-max-MTU-checking.patch
Patch4:	0004-revert-net-add-a-postfix-to-old-ndo_change_mtu.patch
Patch5:	0005-revert-__i40e_setup_tc-changes.patch
Patch6:	0006-revert-net-rename-ndo_setup_tc-callback-and-remove-it-from-.patch
Patch7:	0007-revert-net-mqprio-Modify-mqprio-to-pass-user-parameters-via.patch
Patch8:	0008-revert-net-make-ndo_get_stats64-a-void-function.patch
Patch9:	0009-revert-net-ethernet-update-drivers-to-handle-HWTSTAMP_FILTE.patch
Patch10:	0010-backport-__page_frag_cache_drain.patch
Patch11:	0011-revert-net-propagate-tc-filter-chain-index-down-the-ndo_set.patch
Patch12:	0012-backport-dma_map-unmap_page_attrs.patch
Patch13:	0013-bump-driver-version.patch
Patch14:	0015-add-retpoline-modinfo-flag.patch

%define findpat %( echo "%""P" )
%define __find_requires /usr/lib/rpm/redhat/find-requires.ksyms
%define __find_provides /usr/lib/rpm/redhat/find-provides.ksyms %{kmod_name} %{?epoch:%{epoch}:}%{version}-%{release}
%define sbindir %( if [ -d "/sbin" -a \! -h "/sbin" ]; then echo "/sbin"; else echo %{_sbindir}; fi )
%define dup_state_dir %{_localstatedir}/lib/rpm-state/kmod-dups
%define kver_state_dir %{dup_state_dir}/kver
%define kver_state_file %{kver_state_dir}/%{kmod_kernel_version}.%(arch)
%define dup_module_list %{dup_state_dir}/rpm-kmod-%{kmod_name}-modules

Name:		kmod-redhat-i40e
Version:	%{kmod_driver_version}
Release:	%{kmod_rpm_release}%{?dist}
Summary:	i40e module for Driver Update Program
Group:		System/Kernel
License:	GPLv2
URL:		http://www.kernel.org/
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:	kernel-devel = %kmod_kernel_version redhat-rpm-config kernel-abi-whitelists
ExclusiveArch:	x86_64
%global kernel_source() /usr/src/kernels/%{kmod_kernel_version}.$(arch)

%global _use_internal_dependency_generator 0
Provides:	kernel-modules = %kmod_kernel_version.%{_target_cpu}
Provides:	kmod-%{kmod_name} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires(post):	%{sbindir}/weak-modules
Requires(postun):	%{sbindir}/weak-modules
Requires:	kernel >= 3.10.0-693.el7
Requires:	kernel < 3.10.0-694.el7
%if 0
Requires: firmware(%{kmod_name}) = ENTER_FIRMWARE_VERSION
%endif
%if "%{kmod_build_dependencies}" != ""
BuildRequires:  %{kmod_build_dependencies}
%endif
%if "%{kmod_dependencies}" != ""
Requires:       %{kmod_dependencies}
%endif
# if there are multiple kmods for the same driver from different vendors,
# they should conflict with each other.
Conflicts:	kmod-%{kmod_name}

%description
i40e module for Driver Update Program

This RPM has been provided by Red Hat for testing purposes only and is
NOT supported for any other use. This RPM should NOT be deployed for
purposes other than testing and debugging.
%if 0

%package -n kmod-redhat-i40e-firmware
Version:	ENTER_FIRMWARE_VERSION
Summary:	i40e firmware for Driver Update Program
Provides:	firmware(%{kmod_name}) = ENTER_FIRMWARE_VERSION
Provides:	kernel-modules = %{kmod_kernel_version}.%{_target_cpu}
%description -n  kmod-redhat-i40e-firmware
i40e firmware for Driver Update Program

This RPM has been provided by Red Hat for testing purposes only and is
NOT supported for any other use. This RPM should NOT be deployed for
purposes other than testing and debugging.

%files -n kmod-redhat-i40e-firmware
%defattr(644,root,root,755)
%{FIRMWARE_FILES}

%endif

# Development package
%if 0%{kmod_devel_package}
%package -n kmod-redhat-i40e-devel
Version:	%{kmod_driver_version}
Requires:	kernel >= 3.10.0-693.el7
Requires:	kernel < 3.10.0-694.el7
Summary:	i40e development files for Driver Update Program

%description -n  kmod-redhat-i40e-devel
i40e development files for Driver Update Program

This RPM has been provided by Red Hat for testing purposes only and is
NOT supported for any other use. This RPM should NOT be deployed for
purposes other than testing and debugging.

%files -n kmod-redhat-i40e-devel
%defattr(644,root,root,755)
/usr/share/kmod-%{kmod_vendor}-%{kmod_name}/Module.symvers
%endif

%post
modules=( $(find /lib/modules/%{kmod_kernel_version}.%(arch)/extra/kmod-%{kmod_vendor}-%{kmod_name} | grep '\.ko$') )
printf '%s\n' "${modules[@]}" | %{sbindir}/weak-modules --add-modules --no-initramfs

mkdir -p "%{kver_state_dir}"
touch "%{kver_state_file}"

exit 0

%posttrans
# We have to re-implement part of weak-modules here because it doesn't allow
# calling initramfs regeneration separately
if [ -f "%{kver_state_file}" ]; then
	kver_base="%{kmod_kernel_version}"
	kvers=$(ls -d "/lib/modules/${kver_base%%.*}"*)

	for k_dir in $kvers; do
		k="${k_dir#/lib/modules/}"

		tmp_initramfs="/boot/initramfs-$k.tmp"
		dst_initramfs="/boot/initramfs-$k.img"

		# The same check as in weak-modules: we assume that the kernel present
		# if the symvers file exists.
		if [ -e "/boot/symvers-$k.gz" ]; then
			/usr/bin/dracut -f "$tmp_initramfs" "$k" || exit 1
			cmp -s "$tmp_initramfs" "$dst_initramfs"
			if [ "$?" = 1 ]; then
				mv "$tmp_initramfs" "$dst_initramfs"
			else
				rm -f "$tmp_initramfs"
			fi
		fi
	done

	rm -f "%{kver_state_file}"
	rmdir "%{kver_state_dir}" 2> /dev/null
fi

rmdir "%{dup_state_dir}" 2> /dev/null

exit 0

%preun
if rpm -q --filetriggers kmod 2> /dev/null| grep -q "Trigger for weak-modules call on kmod removal"; then
	mkdir -p "%{kver_state_dir}"
	touch "%{kver_state_file}"
fi

mkdir -p "%{dup_state_dir}"
rpm -ql kmod-redhat-i40e-%{kmod_driver_version}-%{kmod_rpm_release}%{?dist}.$(arch) | \
	grep '\.ko$' > "%{dup_module_list}"

%postun
if rpm -q --filetriggers kmod 2> /dev/null| grep -q "Trigger for weak-modules call on kmod removal"; then
	initramfs_opt="--no-initramfs"
else
	initramfs_opt=""
fi

modules=( $(cat "%{dup_module_list}") )
rm -f "%{dup_module_list}"
printf '%s\n' "${modules[@]}" | %{sbindir}/weak-modules --remove-modules $initramfs_opt

rmdir "%{dup_state_dir}" 2> /dev/null

exit 0

%files
%defattr(644,root,root,755)
/lib/modules/%{kmod_kernel_version}.%(arch)
/etc/depmod.d/%{kmod_name}.conf
/usr/share/doc/kmod-%{kmod_name}/greylist.txt

%prep
%setup -n %{kmod_name}-%{kmod_vendor}-%{kmod_driver_version}

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1
%patch13 -p1
%patch14 -p1
set -- *
mkdir source
mv "$@" source/
mkdir obj

%build
rm -rf obj
cp -r source obj
%{make_build} -C %{kernel_source} V=1 M=$PWD/obj/%{kmod_kbuild_dir} \
	NOSTDINC_FLAGS="-I $PWD/obj/include -I $PWD/obj/include/uapi" \
	EXTRA_CFLAGS="-mindirect-branch=thunk-inline -mindirect-branch-register" \
	%{nil}
# mark modules executable so that strip-to-file can strip them
find obj/%{kmod_kbuild_dir} -name "*.ko" -type f -exec chmod u+x '{}' +

whitelist="/lib/modules/kabi-current/kabi_whitelist_%{_target_cpu}"
for modules in $( find obj/%{kmod_kbuild_dir} -name "*.ko" -type f -printf "%{findpat}\n" | sed 's|\.ko$||' | sort -u ) ; do
	# update depmod.conf
	module_weak_path=$(echo $modules | sed 's/[\/]*[^\/]*$//')
	if [ -z "$module_weak_path" ]; then
		module_weak_path=%{name}
	else
		module_weak_path=%{name}/$module_weak_path
	fi
	echo "override $(echo $modules | sed 's/.*\///') $(echo %{kmod_kernel_version} | sed 's/\.[^\.]*$//').* weak-updates/$module_weak_path" >> source/depmod.conf

	# update greylist
	nm -u obj/%{kmod_kbuild_dir}/$modules.ko | sed 's/.*U //' |  sed 's/^\.//' | sort -u | while read -r symbol; do
		grep -q "^\s*$symbol\$" $whitelist || echo "$symbol" >> source/greylist
	done
done
sort -u source/greylist | uniq > source/greylist.txt

%install
export INSTALL_MOD_PATH=$RPM_BUILD_ROOT
export INSTALL_MOD_DIR=extra/%{name}
make -C %{kernel_source} modules_install \
	M=$PWD/obj/%{kmod_kbuild_dir}
# Cleanup unnecessary kernel-generated module dependency files.
find $INSTALL_MOD_PATH/lib/modules -iname 'modules.*' -exec rm {} \;

install -m 644 -D source/depmod.conf $RPM_BUILD_ROOT/etc/depmod.d/%{kmod_name}.conf
install -m 644 -D source/greylist.txt $RPM_BUILD_ROOT/usr/share/doc/kmod-%{kmod_name}/greylist.txt
%if 0
%{FIRMWARE_FILES_INSTALL}
%endif
%if 0%{kmod_devel_package}
install -m 644 -D $PWD/obj/%{kmod_kbuild_dir}/Module.symvers $RPM_BUILD_ROOT/usr/share/kmod-%{kmod_vendor}-%{kmod_name}/Module.symvers
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Mar 15 2018 Eugene Syromiatnikov <esyr@redhat.com> 2.1.14_k_dup7.4-2.1
- Added modinfo flag for retpoline.
- Resolves: #bz1549986

* Thu Mar 01 2018 Eugene Syromiatnikov <esyr@redhat.com> 2.1.14_k_dup7.4-2
- Rebuilt with -mindirect-branch=thunk-inline -mindirect-branch-register flags.

* Tue Feb 27 2018 Eugene Syromiatnikov <esyr@redhat.com> 2.1.14_k_dup7.4-1
- 141332170ff595319ce42a2cfc2944c2cbb11b4f
- i40e module for Driver Update Program
