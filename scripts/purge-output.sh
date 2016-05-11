#!/bin/bash -l
# Remove any slurm-*.out files older than a few days.
find . -name "logs/slurm-*.out" -mtime +3 -exec rm -vf {} \;
