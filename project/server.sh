#!/bin/bash

case "$1" in
	"start")
		/etc/rc.local &
		;;
	"stop")
		killall uwsgi
		;;
	"restart")
		./server.sh stop
		./server.sh start
		;;
	*)
		echo "Usage: ./server.sh {start|stop|restart}"
		;;
esac