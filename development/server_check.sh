#!/bin/bash

arg_help="Usage: $0 [ quiet ] < crontab | check | start | stop | restart | gitupdate >"

self="$(readlink -f $0)"
uh_path="$(dirname $0)/.."
uh_exec="run_server.py"
uh_pidfile="server.pid"
set -o noglob
uh_args="-d -h * -l server.log -P ${uh_pidfile}"
set +o noglob

function do_crontab
{
  tmpfile=tmpcron
  crontab -l > $tmpfile 2>/dev/null
  echo "*/1 * * * * $self quiet check" >> $tmpfile && \
  crontab $tmpfile
  rm -f $tmpfile
  echo "Added crontab successfully..."
}

function do_git_update
{
  # pull updates
  git pull origin master

  # build gettext objects
  langdir="content/lang"

  declare -A oldlangs
  for lang in $(ls content/lang)
  do
    oldlangs[$lang]=$lang
  done

  echo -n "Updating translations..."
  for file in $(ls po/uh-server/*.po)
  do
    pofile="${file##*/}"
    lang="${pofile%%.*}"
    mkdir -p "$langdir/$lang/LC_MESSAGES/"
    msgfmt "$file" -o "$langdir/$lang/LC_MESSAGES/unknown-horizons-server.mo"
    unset oldlangs[$lang]
  done

  # house keeping
  for i in "${!oldlangs[@]}"
  do
    rm -rf "$langdir/$i"
  done
  echo "done"
}

function debug
{
  [ -n "$DEBUG" ] && echo $*
}

function get_pid
{
  pid=0
  local _pidfile=$1
  if [ ! -f "$_pidfile" ]
  then
    debug "Pid file ($_pidfile) doesn't exist. Process not running?"
    return
  fi
  read pid < $_pidfile

  if [ "$pid" -le 0 ]
  then
    debug "Invalid pid in pidfile: $pid"
    return
  fi

  local _proc=$(ps -ww -o pid= -p $pid 2>/dev/null)
  if [ -z "$_proc" ]
  then
    _echo "Process isn't running any more. Maybe died?"
    pid=0
  fi
}

if [ "$1" = "quiet" ]
then
  SILENT=1
  shift
fi
function _echo
{
  [ -z "$SILENT" ] && echo $*
}

function start
{
  _echo -n "Starting server..."
  set -o noglob
  ./${uh_exec} ${uh_args}
  set +o noglob
  _echo "done"
}

function stop
{
  get_pid $uh_pidfile
  if [ "$pid" -gt 0 ]
  then
    _echo -n "Stopping server (pid=$pid)"
    kill -TERM $pid
    _echo "...done"
  fi
  [ -f "$uh_pidfile" ] && rm -f $uh_pidfile
}

cd "$uh_path"
case "$1" in
  crontab)
    do_crontab
    exit
    ;;
  check)
    get_pid $uh_pidfile
    if [ "$pid" -eq 0 ]
    then
      echo "Server not running. Starting..."
      start
    fi
    ;;
  stop)
    stop
    ;;
  start)
    start
    ;;
  restart)
    stop
    start
    ;;
  gitupdate)
    stop
    do_git_update
    start
    ;;
  *)
    echo $arg_help
    ;;
esac
