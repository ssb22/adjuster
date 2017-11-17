#!/bin/bash
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/adjuster.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/annogen.py
wget -N http://people.ds.cam.ac.uk/ssb22/adjuster/termlayout.py
git commit -am update && git push
