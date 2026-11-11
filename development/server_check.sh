#!/bin/bash

arg_help="Usage: $0 [ quiet ] < crontab | check | start | stop | restart | gitupdate >"

self="$(readlink -f "$0")"
uh_path="$(dirname "$0")/.."
uh_exec="run_server.py"
uh_pidfile="server.pid"
set -o noglob
uh_args="-d -h * -l server.log -P ${uh_pidfile}"
set +o noglob

function do_crontab
{
  tmpfile=tmpcron
  crontab -l 2>/dev/null | grep -vF "*/1 * * * * $self quiet check" > "$tmpfile" || true
  echo "*/1 * * * * $self quiet check" >> "$tmpfile"

  if crontab "$tmpfile"; then
    echo "Added crontab successfully..."
  else
    echo "Failed to install crontab." >&2
    rm -f "$tmpfile"
    return 1
  fi
  rm -f "$tmpfile"
}

function do_git_update
{
  # pull updates
  if ! git pull origin master; then
    echo "git pull failed; aborting update." >&2
    return 1
  fi

  # build gettext objects
  langdir="content/lang"

  declare -A oldlangs
  # glob instead of $(ls ...); keys must stay bare names, since the
  # housekeeping loop below removes "$langdir/$i".
  for langpath in "$langdir"/*
  do
    lang=$(basename "$langpath")
    oldlangs[$lang]=$lang
  done

  echo -n "Updating translations..."
  for file in po/uh-server/*.po
  do
    [ -f "$file" ] || continue   # glob stays literal when nothing matches
    pofile="${file##*/}"
    lang="${pofile%%.*}"
    mkdir -p "$langdir/$lang/LC_MESSAGES/"
    msgfmt "$file" -o "$langdir/$lang/LC_MESSAGES/unknown-horizons-server.mo"
    # shellcheck disable=SC2184
unset oldlangs["$lang"]
  done

  # house keeping
  for i in "${!oldlangs[@]}"
  do
    rm -rf "${langdir:?}/$i"
  done
  echo "done"
}

function debug
{
  [ -n "$DEBUG" ] && echo "$@"
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
  read -r pid < "$_pidfile"
  pid=${pid:-0}

  if [ "$pid" -le 0 ]
  then
    debug "Invalid pid in pidfile: $pid"
    return
  fi

  local _proc
_proc=$(ps -ww -o pid= -p "$pid" 2>/dev/null)
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
  [ -z "$SILENT" ] && echo "$@"
}

function start
{
  _echo -n "Starting server..."
  set -o noglob
  ./"${uh_exec}" "${uh_args}"
  set +o noglob
  _echo "done"
}

function stop
{
  get_pid $uh_pidfile
  if [ "$pid" -gt 0 ]
  then
    _echo -n "Stopping server (pid=$pid)"
    kill -TERM "$pid"
    _echo "...done"
  fi
  rm -f "$uh_pidfile"
}

cd "$uh_path" || exit
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
    do_git_update || exit 1
    start
    ;;
  *)
    echo "$arg_help"
    ;;
esac
