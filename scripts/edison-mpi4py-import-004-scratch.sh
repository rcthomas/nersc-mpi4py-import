#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=edison-mpi4py-import-004-scratch
#SBATCH --license=SCRATCH
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=24
#SBATCH --output=logs/slurm-edison-mpi4py-import-004-scratch-%j.out
#SBATCH --partition=regular
#SBATCH --qos=normal
#SBATCH --time=20

# Configuration.

commit=true
debug=false

# Load modules.

module unload python
module swap PrgEnv-intel PrgEnv-gnu
module load python_base

# Optional debug output.

if [ $debug = true ]; then
    module list
    set -x
fi

# Stage and activate virtualenv.

benchmark_src=/global/common/edison/usg/python/mpi4py-import
benchmark_dest=$SCRATCH/staged-mpi4py-import
benchmark_path=$benchmark_dest/mpi4py-import

mkdir -p $benchmark_dest
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
