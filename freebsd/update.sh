#!/bin/bash
set -e
git pull
echo "PORTNAME=		adjuster" > m
echo "DISTVERSIONPREFIX=	v" >> m
export Tags=$(git describe --tags|sed -e s/v//)
echo "DISTVERSION=		$(echo "$Tags"|sed -e 's/-[^-]*$//')" >> m
if echo "$Tags"|grep '\-' >/dev/null; then echo "DISTVERSIONSUFFIX=	$(echo "$Tags"|sed -e 's/.*\(-[^-]*\)$/\1/')" >> m; fi # else we're at a version point without extra commits
grep -v ^DIST < Makefile | grep -v ^PORTNAME >> m
mv m Makefile
# ssh freebsd pkg install portlint
# ssh freebsd "echo 'DEVELOPER=yes' >> /etc/make.conf"
#ssh freebsd git config --global user.email ..
#ssh freebsd 'git config --global user.name ""'
ssh freebsd mkdir -p /usr/ports/www/adjuster/
scp Makefile pkg-descr freebsd:/usr/ports/www/adjuster/
ssh freebsd 'cd /usr/ports/www/adjuster/ && touch distinfo && git add Makefile pkg-descr distinfo'
ssh freebsd 'cd /usr/ports/www/adjuster/ && rm -rf work distinfo && make makesum && portlint -A && (make deinstall || true) && make install && rm -rf work && git add * && git commit * -m "www/adjuster '"$(grep -m 1 '^"Web' ../adjuster.py|cut -d ' ' -f3)"'"'
ssh freebsd 'cd /usr/ports && git format-patch --stdout -1' > adjuster.mbox
echo "adjuster.mbox to https://bugs.freebsd.org/bugzilla/enter_bug.cgi (as attachment with Content Type set to Patch: use Choose File not copy-paste)"
echo "If the diff is wrong and we need to re-run update.sh after a change, first do: ssh freebsd 'cd /usr/ports;git reset --hard HEAD~1'"
