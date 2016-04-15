#!/bin/bash
# Remove any slurm-*.out files older than a day.
find . -name "slurm-*.out" -mtime +3 -exec rm -f {} \;

