#!/bin/bash
git pull --no-edit
wget -N http://ssb22.user.srcf.net/adjuster/adjuster.py
wget -N http://ssb22.user.srcf.net/adjuster/annogen.py
wget -N http://ssb22.user.srcf.net/adjuster/termlayout.py
wget -N http://ssb22.user.srcf.net/adjuster/tmux-annotator.sh

(
    awk -- 'BEGIN {p=1} /Options for Web Adjuster/ {p=0} // {if(p) print}' < README.md
    python adjuster.py --markdown-options
    echo;echo Annotator Generator command line;echo ===========================;echo
    COLUMNS=32767 python annogen.py --help 2>/dev/null|sed -e 's/^  \([^ ]\)/\n`\1/' -e 's,   *,`\n : ,' -e 's,BEFORE,**before**,g' -e 's,AFTER,**after**,g' -e 's,ALWAYS,**always**,g' -e 's, ALL , **all** ,g' -e 's, LONG , **long** ,g' -e 's, NOT , **not** ,g' -e 's, TOTAL , **total** ,g' -e 's,DEPRECATED,**Deprecated**,g' -e 's, WITHOUT , **without** ,g' -e 's/\(<[^ ]*\)/`\1`/g'
    echo;echo Copyright and Trademarks;echo ========================;echo
    cat <<EOF
(c) Silas S. Brown, licensed under Apache 2

* Android is a trademark of Google LLC.

* Apache is a registered trademark of The Apache Software Foundation.

* AppEngine is possibly a trademark of Google LLC.

* Apple is a trademark of Apple Inc.

* Firefox is a registered trademark of The Mozilla Foundation.

* Google Play is a trademark of Google LLC.

* Google is a trademark of Google LLC.

* Java is a registered trademark of Oracle Corporation in the US and possibly other countries.

* Javascript is a trademark of Oracle Corporation in the US.

* Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.

* MP3 is a trademark that was registered in Europe to Hypermedia GmbH Webcasting but I was unable to confirm its current holder.

* Mac is a trademark of Apple Inc.

* Microsoft is a registered trademark of Microsoft Corp.

* Python is a trademark of the Python Software Foundation.

* Raspberry Pi is a trademark of the Raspberry Pi Foundation.

* Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.

* Windows is a registered trademark of Microsoft Corp.

* iPhone is a trademark of Apple in some countries.

* Any other trademarks I mentioned without realising are trademarks of their respective holders.
EOF
    ) > n && mv n README.md

git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g' -e 's/git-sync.sh/git-sync script/' -e 's/adjuster.py/Web Adjuster/' -e 's/annogen.py/Annotator Generator/' -e 's/termlayout.py/TermLayout/')" && git push
