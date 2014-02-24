#!/bin/bash
# sync Web Adjuster to SVN
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
svn commit -m "Update adjuster.py"
