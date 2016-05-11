#!/bin/bash -l

# Run this once a month.

path=nersc-mpi4py-import/logs/$(date +"%Y" -d "-1 month")
month=$(date +"%Y-%m" -d "-1 month")
files=$(find . -name "slurm*.out" -newermt "$month-01" -and -not -newermt "$month-01 +1 month -1 sec" -printf "%p ")

[ -n "$files" ] && hsi mkdir -p $path && htar -cvf $path/$month.tar $files && rm -vf $files
