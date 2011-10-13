#!/bin/bash

cd "$(dirname $0)"

function create()
{
  rrdtool create uh.rrd
    --start N --step 60
    DS:games_total:GAUGE:300:0:1000
    DS:games_playing:GAUGE:300:0:1000
    DS:players_total:GAUGE:300:0:1000
    DS:players_lobby:GAUGE:300:0:1000
    DS:players_playing:GAUGE:300:0:1000
    RRA:AVERAGE:0.5:1:11520
    RRA:AVERAGE:0.5:10:4608
    RRA:AVERAGE:0.5:360:1464
    RRA:MIN:0.5:1:11520
    RRA:MIN:0.5:10:4608
    RRA:MIN:0.5:360:1464
    RRA:MAX:0.5:1:11520
    RRA:MAX:0.5:10:4608
    RRA:MAX:0.5:360:1464
    RRA:LAST:0.5:1:11520
    RRA:LAST:0.5:10:4608
    RRA:LAST:0.5:360:1464

  rrdtool create traffic.rrd
    --start N --step 60
    DS:in:COUNTER:300:0:U
    DS:out:COUNTER:300:0:U
    RRA:AVERAGE:0.5:1:11520
    RRA:AVERAGE:0.5:10:4608
    RRA:AVERAGE:0.5:360:1464
    RRA:MIN:0.5:1:11520
    RRA:MIN:0.5:10:4608
    RRA:MIN:0.5:360:1464
    RRA:MAX:0.5:1:11520
    RRA:MAX:0.5:10:4608
    RRA:MAX:0.5:360:1464
    RRA:LAST:0.5:1:11520
    RRA:LAST:0.5:10:4608
    RRA:LAST:0.5:360:1464
}

function update()
{
  statfile="$1"
  if [ ! -r "$statfile" ]
  then
    echo "Unable to read statistics file: $statfile"
    exit 1
  fi

  while read t v
  do
    case "$t" in
      Games.Total:)
        gtotal=$v
        ;;
      Games.Playing:)
        gplaying=$v
        ;;
      Players.Total:)
        ptotal=$v
        ;;
      Players.Lobby:)
        plobby=$v
        ;;
      Players.Playing:)
        pplaying=$v
        ;;
    esac
    val=$t
  done < "$statfile"

  rrdtool update uh.rrd "N:$gtotal:$gplaying:$ptotal:$plobby:$pplaying"

  # freebsd specific
  stats=($(netstat -bI "rl0" | grep "<Link#.*>" | awk -F" " '{ print $7" "$10 }'))
  rrdtool update traffic.rrd "N:${stats[0]}:${stats[1]}"
}

datestr=$(date)
datestr=${datestr//:/\\:}

function graph()
{
  gext="png"
  gprefix=""
  gsuffix=""
  rrdoptions_common=()

  subcmd="$1"
  shift
  case "$subcmd" in
    daily)
      gtype="Day"
      gsuffix="_day"
      gstart="-86400"
      gend="-60"
      rrdoptions_common=(
        ${rrdoptions_common[@]}
        --x-grid="MINUTE:30:HOUR:2:HOUR:2:0:%H:%M"
      )
      ;;
    weekly)
      gtype="Week"
      gsuffix="_week"
      gstart="-604800"
      gend="-1800"
      ;;
    monthly)
      gtype="Month"
      gsuffix="_month"
      gstart="-2678400"
      gend="-7200"
      ;;
    yearly)
      gtype="Year"
      gsuffix="_year"
      gstart="-33053184"
      gend="-86400"
      ;;
    all)
      graph "daily" $*
      graph "weekly" $*
      graph "monthly" $*
      graph "yearly" $*
      ;;
    *)
      echo "$0: $cmd <subcommand>"
      echo "subcommands: daily, weekly, monthly, yearly, all"
      exit 1
      ;;
  esac

  rrdoptions_common=(
    ${rrdoptions_common[@]}
    --imgformat=PNG
    --start=$gstart
    --end=$gend
    --height=120
    --width=500
    --slope-mode
    --alt-autoscale-max
    --lower-limit=0
    --rigid
    --color="CANVAS#504848"
  )
  graph_games_players $*
  graph_games $*
  graph_players $*
  graph_traffic $*
}

function graph_games_players()
{
  gname="games_players"
  rrdoptions=(
    ${rrdoptions_common[@]}
    --title="Unknown Horizons - Master Server Games & Players"
    --base=1000
    DEF:games=uh.rrd:games_total:AVERAGE
    CDEF:games_f=games,FLOOR
    DEF:players=uh.rrd:players_total:AVERAGE
    CDEF:players_f=players,FLOOR
    AREA:players#2CADEF35:""
    LINE1:players#2CADEFFF:"Players"
    LINE1:games#E16000FF:"Games"
    COMMENT:" \\c"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"Players  "
    GPRINT:players_f:LAST:"Current\:%9.2lf  "
    GPRINT:players:AVERAGE:"Average\:%9.2lf  "
    GPRINT:players_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"Games    "
    GPRINT:games_f:LAST:"Current\:%9.2lf  "
    GPRINT:games:AVERAGE:"Average\:%9.2lf  "
    GPRINT:games_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"$gtype @ $datestr\\r"
  )
  graph_do $*
}


function graph_games()
{
  gname="games"
  rrdoptions=(
    ${rrdoptions_common[@]}
    --title="Unknown Horizons - Master Server Games"
    --base=1000
    DEF:total=uh.rrd:games_total:AVERAGE
    CDEF:total_f=total,FLOOR
    DEF:playing=uh.rrd:games_playing:AVERAGE
    CDEF:playing_f=playing,FLOOR
    AREA:total#2CADEF35:""
    LINE1:total#2CADEFFF:"Total"
    LINE1:playing#E16000FF:"Running"
    COMMENT:" \\c"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"Total    "
    GPRINT:total_f:LAST:"Current\:%9.2lf  "
    GPRINT:total:AVERAGE:"Average\:%9.2lf  "
    GPRINT:total_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"Running  "
    GPRINT:playing_f:LAST:"Current\:%9.2lf  "
    GPRINT:playing:AVERAGE:"Average\:%9.2lf  "
    GPRINT:playing_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"$gtype @ $datestr\\r"
  )
  graph_do $*
}

function graph_players()
{
  gname="players"
  rrdoptions=(
    ${rrdoptions_common[@]}
    --title="Unknown Horizons - Master Server Players"
    --base=1000
    DEF:total=uh.rrd:players_total:AVERAGE
    CDEF:total_f=total,FLOOR
    DEF:playing=uh.rrd:players_playing:AVERAGE
    CDEF:playing_f=playing,FLOOR
    DEF:lobby=uh.rrd:players_lobby:AVERAGE
    CDEF:lobby_f=lobby,FLOOR
    AREA:total#2CADEF35:""
    LINE1:total#2CADEFFF:"Total"
    LINE1:playing#E16000FF:"Playing"
    LINE1:lobby#00CF00FF:"In Lobby"
    COMMENT:" \\c"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"Total    "
    GPRINT:total_f:LAST:"Current\:%9.2lf  "
    GPRINT:total:AVERAGE:"Average\:%9.2lf  "
    GPRINT:total_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"Playing  "
    GPRINT:playing_f:LAST:"Current\:%9.2lf  "
    GPRINT:playing:AVERAGE:"Average\:%9.2lf  "
    GPRINT:playing_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"In Lobby "
    GPRINT:lobby_f:LAST:"Current\:%9.2lf  "
    GPRINT:lobby:AVERAGE:"Average\:%9.2lf  "
    GPRINT:lobby_f:MAX:"Maximum\:%9.2lf  \\r"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"$gtype @ $datestr\\r"
  )
  graph_do $*
}

function graph_traffic()
{
  gname="traffic"
  rrdoptions=(
    ${rrdoptions_common[@]}
    --title="Unknown Horizons - Master Server Traffic"
    --base=1000
    DEF:in=traffic.rrd:in:AVERAGE
    DEF:out=traffic.rrd:out:AVERAGE
    CDEF:inb=in,8,*
    CDEF:outb=out,8,*
    AREA:inb#2CADEF35:""
    LINE1:inb#2CADEFFF:"Inbound"
    LINE1:outb#E16000FF:"Outbound"
    COMMENT:" \\c"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"Inbound "
    GPRINT:inb:LAST:"Current\:%8.2lf %s "
    GPRINT:inb:AVERAGE:"Average\:%8.2lf %s "
    GPRINT:inb:MAX:"Maximum\:%8.2lf %s  \\r"
    COMMENT:"Outbound"
    GPRINT:outb:LAST:"Current\:%8.2lf %s "
    GPRINT:outb:AVERAGE:"Average\:%8.2lf %s "
    GPRINT:outb:MAX:"Maximum\:%8.2lf %s  \\r"
    COMMENT:"-----------------------------------------------------------------------  \\r"
    COMMENT:"$gtype @ $datestr\\r"
  )
  graph_do $*
}

function graph_do()
{
  filename="${gprefix}${gname}${gsuffix}.${gext}"
  rrdtool graph - "${rrdoptions[@]}" > "$filename"
}

function usage()
{
  echo "$0: <command>"
  echo "commands: create, update, graph"
  exit 1
}

cmd="$1"
shift
case "$cmd" in
  create)
    create $*
    ;;
  update)
    update $*
    ;;
  graph)
    graph $*
    ;;
  *)
    usage
    ;;
esac
