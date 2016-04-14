#!/bin/bash -l
benchmarks=($(ls $1*.sh))
n_benchmarks=${#benchmarks[*]}
selected_benchmark=${benchmarks[$((RANDOM%n_benchmarks))]}
[ -z "$(squeue -u rthomas -o '\%35j' | grep ${selected_benchmark%.sh})" ] && sbatch $selected_benchmark
