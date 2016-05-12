#!/bin/bash -l

# module load git
# git pull

benchmarks=($(ls $1*.sh))
n_benchmarks=${#benchmarks[*]}
selected_benchmark=${benchmarks[$((RANDOM%n_benchmarks))]}
[ -z "$(squeue -u $USER -o '\%35j' | grep ${selected_benchmark%.sh})" ] && sbatch $selected_benchmark
