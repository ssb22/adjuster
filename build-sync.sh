#!/bin/bash
# sync Web Adjuster and Annotator Generator to SVN
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.py
svn commit -m "Update adjuster/annogen"
