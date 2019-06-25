#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/termlayout.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/tmux-annotator.sh
git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g' -e 's/git-sync.sh/git-sync script/' -e 's/adjuster.py/Web Adjuster/' -e 's/annogen.py/Annotator Generator/' -e 's/termlayout.py/TermLayout/')" && git push
