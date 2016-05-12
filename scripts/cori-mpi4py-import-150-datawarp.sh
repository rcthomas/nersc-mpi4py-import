#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=cori-mpi4py-import-150-datawarp
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=150
#SBATCH --ntasks-per-node=32
#SBATCH --output=logs/slurm-cori-mpi4py-import-150-datawarp-%j.out
#SBATCH --partition=regular
#SBATCH --qos=normal
#SBATCH --time=40
#DW jobdw capacity=2TB access_mode=striped type=scratch

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

benchmark_src=/usr/common/software/python/mpi4py-import
benchmark_dest=$DW_JOB_STRIPED
benchmark_path=$benchmark_dest/mpi4py-import

time rsync -az --exclude "*.pyc" $benchmark_src $benchmark_dest
sed -i "s|^VIRTUAL_ENV=.*$|VIRTUAL_ENV=\"$benchmark_path\"|" $benchmark_path/bin/activate
source $benchmark_path/bin/activate

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
python -c "import astropy; print astropy.__path__"
strace python -c "import astropy" 2>&1 | grep "open(" | wc

# Allows up to 5 minutes for pynamic-pyMPI to MPI_Init().

export PMI_MMAP_SYNC_WAIT_TIME=300

# Run benchmark.

output=latest-$SLURM_JOB_NAME.txt
time srun python mpi4py-import.py $(date +%s) | tee $output

# Finalize benchmark result.

if [ $commit = true ]; then
    module load mysqlpython
    python report-benchmark.py finalize $( grep elapsed $output | awk '{ print $NF }' )
fi
