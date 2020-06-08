#!/bin/bash

# use GNU parallel to run multiple repetitions and scenarios in parallel
# run from project root! (where Readme is)
start=`date +%s`
printf "\n------------------Started running the script-------------------------\n"
parallel bjointsp-adapter ::: "--network" :::: scripts/network_files.txt ::: "--service_functions" :::: scripts/service_files.txt ::: "--config" :::: scripts/config_files.txt ::: "--iterations" ::: "200" ::: "--seed" :::: scripts/30seeds.txt

stop=`date +%s`
runtime=$((stop-start))
printf "\n\nRunning the script took %d seconds\n" $runtime