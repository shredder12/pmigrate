#!/bin/bash

count=0
while [ 0 ]
do
	sleep 2
        count=$(expr $count + 1)
        echo $count >> /tmp/results
done
