#!/bin/bash
# Remove any slurm-*.out files older than a day.
find . -name "slurm-*.out" -mtime +1 -exec rm -f {} \;

