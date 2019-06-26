#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/termlayout.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/tmux-annotator.sh

(
    awk -- 'BEGIN {p=1} /Options for Web Adjuster/ {p=0} /./ {if(p) print}' < README.md
    python adjuster.py --markdown-options
    echo;echo Annotator Generator command line;echo ===========================;echo
    COLUMNS=32767 python annogen.py --help 2>/dev/null|sed -e 's/^  \([^ ]\)/\n`\1/' -e 's,  ,`\n : ,' -e 's,BEFORE,**before**,g' -e 's,AFTER,**after**,g' -e 's,ALWAYS,**always**,g' -e 's, ALL , **all** ,g' -e 's, LONG , **long** ,g' -e 's, NOT , **not** ,g' -e 's,DEPRECATED,**Deprecated**,g' -e 's, WITHOUT , **without** ,g' -e 's/\(<[^ ]*\)/`\1`/g'
    ) > n && mv n README.md

git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g' -e 's/git-sync.sh/git-sync script/' -e 's/adjuster.py/Web Adjuster/' -e 's/annogen.py/Annotator Generator/' -e 's/termlayout.py/TermLayout/')" && git push
