for x in 10001 10000 11000 11001 10002 10003 10004 10005 10006 10007 10008
do
	echo "killing at port" $x
	var=$(lsof -i:$x | grep -o " [0-9]\+ "|grep -o "[0-9]\+")
	kill $var
done