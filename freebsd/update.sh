#!/bin/bash
# ssh freebsd pkg install portlint
# ssh freebsd "echo 'DEVELOPER=yes' >> /etc/make.conf"
scp Makefile pkg-descr freebsd:/usr/ports/www/adjuster/ || exit 1
ssh freebsd 'cd /usr/ports/www/adjuster/ && rm -f distinfo && make makesum && portlint -A && git add * && git commit * -m "www/adjuster '"$(grep -m 1 '^"Web' ../adjuster.py|cut -d ' ' -f3)"'" && git format-patch --stdout -1' > adjuster.mbox &&
echo "adjuster.mbox to https://bugs.freebsd.org/bugzilla/enter_bug.cgi (as plain-text attachment if possible)"
