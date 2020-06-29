#!/bin/bash

# use GNU parallel to run multiple repetitions and scenarios in parallel
# run from project root! (where Readme is)
printf "\n------------------Started running the script-------------------------\n"
parallel --bar bjointsp-adapter ::: "--network" :::: scripts/network_files.txt ::: "--service_functions" :::: scripts/service_files.txt ::: "--config" :::: scripts/config_files.txt ::: "--iterations" ::: "1000" ::: "--seed" :::: scripts/30seeds.txt

printf "\n\nFinished running the script\n"