#!/bin/bash
set -e

if [ -e /etc/make.conf ] && ! [ -e $HOME/.gitconfig ]; then
    # if running _on_ FreeBSD and git not yet set up, must do that first: it's picky about ownership even when fetching tags
    git config --global user.name "Silas S. Brown"
    git config --global user.email ssb22$(echo @)cam.ac.uk
    cd ..
    git config --global --add safe.directory $(pwd)
    for N in $(find . -type d); do git config --global --add safe.directory $(pwd)/$N; done
    cd freebsd
fi

# update Makefile to actual current version
echo "PORTNAME=		adjuster" > m
echo "DISTVERSIONPREFIX=	v" >> m
export Tags=$(git describe --tags|sed -e s/v//)
echo "DISTVERSION=		$(echo "$Tags"|sed -e 's/-[^-]*$//')" >> m
if echo "$Tags"|grep '\-' >/dev/null; then echo "DISTVERSIONSUFFIX=	$(echo "$Tags"|sed -e 's/.*\(-[^-]*\)$/\1/')" >> m; fi # else we're at a version point without extra commits
grep -v ^DIST < Makefile | grep -v ^PORTNAME >> m
mv m Makefile

# create adjuster.mbox
if [ -e /etc/make.conf ] ; then
    # we're running _on_ a FreeBSD system: assume we're root
    pkg info portlint || pkg install -y portlint
    grep DEVELOPER=yes /etc/make.conf 2>/dev/null || echo 'DEVELOPER=yes' >> /etc/make.conf
    if ! [ -d /usr/ports ] ; then git clone --depth 1 https://github.com/freebsd/freebsd-ports /usr/ports; fi # use the mirror to save upstream bandwidth: we're not going to push from here
    mkdir -p /usr/ports/www/adjuster/
    cp Makefile pkg-descr /usr/ports/www/adjuster/
    OldDir=$(pwd)
    cd /usr/ports/www/adjuster/
    rm -rf work distinfo
    make makesum
    portlint -A
    make deinstall || true
    make install
    rm -rf work
    git add *
    git commit * -m "www/adjuster '"$(grep -m 1 '^"Web' $OldDir/../adjuster.py|cut -d ' ' -f3)
    cd /usr/ports
    git format-patch --stdout -1 > $OldDir/adjuster.mbox
else
    # assume we can ssh to the FreeBSD box as root
    ssh freebsd "pkg info portlint || pkg install -y portlint"
    ssh freebsd "grep DEVELOPER=yes /etc/make.conf 2>/dev/null || echo 'DEVELOPER=yes' >> /etc/make.conf"
    ssh freebsd "if ! [ -e .gitconfig ]; then git config --global user.name 'Silas S. Brown'; git config --global user.email ssb22$(echo @)cam.ac.uk ; fi"
ssh freebsd mkdir -p /usr/ports/www/adjuster/
scp Makefile pkg-descr freebsd:/usr/ports/www/adjuster/
ssh freebsd 'cd /usr/ports/www/adjuster/ && rm -rf work distinfo && make makesum && portlint -A && (make deinstall || true) && make install && rm -rf work && git add * && git commit * -m "www/adjuster '"$(grep -m 1 '^"Web' ../adjuster.py|cut -d ' ' -f3)"'"'
ssh freebsd 'cd /usr/ports && git format-patch --stdout -1' > adjuster.mbox
fi
echo "adjuster.mbox to https://bugs.freebsd.org/bugzilla/enter_bug.cgi (as attachment with Content Type set to Patch: use Choose File not copy-paste)"
echo "If the diff is wrong and we need to re-run update.sh after a change, first do: ssh freebsd 'cd /usr/ports;git reset --hard HEAD~1'"
