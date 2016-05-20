#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=edison-mpi4py-import-004-tmpfs
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=24
#SBATCH --output=logs/slurm-edison-mpi4py-import-004-tmpfs-%j.out
#SBATCH --partition=regular
#SBATCH --qos=normal
#SBATCH --time=20

# Configuration.

commit=true
debug=false

# Load modules.

module unload python
module unload altd
module swap PrgEnv-intel PrgEnv-gnu
module load python_base

# Optional debug output.

if [ $debug = true ]; then
    module list
    set -x
fi

# Stage and activate virtualenv.

benchmark_src=/usr/common/usg/python/mpi4py-import
benchmark_dest=/dev/shm/mpi4py-import/$SLURM_JOBID
benchmark_path=$benchmark_dest/mpi4py-import

srun -n $SLURM_JOB_NUM_NODES mkdir -p $benchmark_dest
sleep 5
time srun -n $SLURM_JOB_NUM_NODES rsync -az --exclude "*.pyc" $benchmark_src $benchmark_dest
sleep 5
srun -n $SLURM_JOB_NUM_NODES sed -i "s|^VIRTUAL_ENV=.*$|VIRTUAL_ENV=\"$benchmark_path\"|" $benchmark_path/bin/activate
sleep 5
source $benchmark_path/bin/activate
sleep 5

# Initialize benchmark result.

if [ $commit = true ]; then
    module load mysql
    module load mysqlpython
    python report-benchmark.py initialize
    module unload mysqlpython
fi

# Sanity checks, re-generate bytecode files.

which python
echo PYTHONPATH: $PYTHONPATH
python -c 'import sys; print "\n".join( sys.path )'
python -c "import astropy; print astropy.__path__"
strace python -c "import astropy" 2>&1 | grep "open(" | wc

# Run benchmark.

output=latest-$SLURM_JOB_NAME.txt
time srun python mpi4py-import.py $(date +%s) | tee $output

# Finalize benchmark result.

if [ $commit = true ]; then
    module load mysqlpython
    python report-benchmark.py finalize $( grep elapsed $output | awk '{ print $NF }' )
fi
