#!/bin/bash -l
[ -z "`squeue -u rthomas -o '\%30j' | grep $1`" ] && sbatch $1.sh
