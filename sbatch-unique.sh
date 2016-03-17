#!/bin/bash -l
[ -z "`squeue -u rthomas -o '\%35j' | grep $1`" ] && sbatch $1.sh
