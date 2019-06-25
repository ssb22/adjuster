#!/bin/bash

# tmux-annotator

# This script runs a tmux session and binds the F4 key to
# annotate the current screen using "annotator" (in PATH)
# and pipes the result through "termlayout" (in PATH).

# Silas S. Brown 2014, 2015, 2019 - public domain - no warranty

if [ "$TMUX" ]; then
  # tmux is not already running
  exec tmux new-session '"'"$0"'"'" shell $*"
elif [ "$1" = annot ]; then
  tmux last-window
  tmux capture-pane
  tmux last-window
  clear ; echo Please wait... # hopefully not long
  if test -e /dev/shm; then export TmpFile=$(mktemp /dev/shm/annotXXX)
  else export TmpFile=$(mktemp /tmp/annotXXX); fi
  tmux save-buffer $TmpFile # can't put /dev/stdout here
  tmux delete-buffer
  sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/$/<br>/' < $TmpFile | annotator --ruby | termlayout | less -r
  rm -f $TmpFile
else
  tmux bind-key -n F4 new-window '"'"$0"'"'" annot"
  echo "F4 = run annotator"
  if [ "$1" = shell ]; then
    shift
    if [ ! "$1" ]; then
      exec "$SHELL" || exec /bin/bash
    else "$@"; fi
  elif ! [ ! "$1" ]; then "$@"; fi
fi
