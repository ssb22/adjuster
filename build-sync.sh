#!/bin/bash
# sync Web Adjuster and Annotator Generator to SVN
# also TermLayout
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/termlayout.py
svn commit -m "Update adjuster/annogen/termlayout"
