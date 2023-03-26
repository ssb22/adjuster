#!/bin/bash
set -e
# ssh freebsd pkg install portlint
# ssh freebsd "echo 'DEVELOPER=yes' >> /etc/make.conf"
ssh freebsd mkdir -p /usr/ports/www/adjuster/
scp Makefile pkg-descr freebsd:/usr/ports/www/adjuster/
ssh freebsd 'cd /usr/ports/www/adjuster/ && touch distinfo && git add Makefile pkg-descr distinfo'
ssh freebsd 'cd /usr/ports/www/adjuster/ && rm -rf work distinfo && make makesum && portlint -A && git add * && git commit * -m "www/adjuster '"$(grep -m 1 '^"Web' ../adjuster.py|cut -d ' ' -f3)"'"'
ssh freebsd 'cd /usr/ports && git format-patch --stdout -1' > adjuster.mbox
echo "adjuster.mbox to https://bugs.freebsd.org/bugzilla/enter_bug.cgi (as plain-text attachment if possible)"
