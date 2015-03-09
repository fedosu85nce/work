%post
/sbin/mpathconf --enable

echo -e "# Load ap.ko at boot\nap" > /etc/modules-load.d/zkvm.conf
sed -i '/^Description/a\ConditionPathExists=/dev/hwrng' /usr/lib/systemd/system/rngd.service
sed -i 's/^ExecStart=\/sbin\/rngd -f$/& --rng-device=\/dev\/hwrng/' /usr/lib/systemd/system/rngd.service

%end
