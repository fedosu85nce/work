= Announcements =

This README.txt explains how to generate an e-mail and wiki page about
PowerKVM releases to be announced using /bin/announcement.sh script.

=== Edit variables ===

Update the following variables in ./config/vars:

RELEASE_ISO_ID
BASE_VER
ISO_MD5
NETBOOT_TARBALL_MD5
EMAIL_CONTACT

If you need to add a new variable to be expanded in the templates, do
not forget to add its name in the VARS list.
There are small differences for 2.1.0 and 2.1.1 URLs.

=== Update changelog ===

Update file ./templates/changes.txt with the changes for this release.

=== Update bugs fixed ===

Update file ./templates/bugs-fixed.txt with the list of fixed bugs in
this release.

=== Update bugs opened ===

Update file ./templates/bugs-opened.txt with the list of still opened
bugs.

=== Generate e-mail for announcement ===

./bin/announcement.sh --email

=== Generate e-mail for updates announcement ===

./bin/announcement.sh --email-updates

=== Generate wiki page ===

./bin/announcement.sh --wiki
