#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=edison-mpi4py-import-004-common
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=24
#SBATCH --output=logs/slurm-edison-mpi4py-import-004-common-%j.out
#SBATCH --partition=regular
#SBATCH --qos=normal
#SBATCH --time=5

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

benchmark_path=/usr/common/usg/python/mpi4py-import
source $benchmark_path/bin/activate

# Initialize benchmark result.

if [ $commit = true ]; then
    module load mysql
    module load mysqlpython
    python report-benchmark.py initialize
    module unload mysqlpython
fi

# Sanity checks.

which python
echo PYTHONPATH: $PYTHONPATH
python -c "import numpy; print numpy.__path__"
strace python -c "import numpy" 2>&1 | grep "open(" | wc

# Run benchmark.

output=latest-$SLURM_JOB_NAME.txt
time srun python mpi4py-import.py $(date +%s) | tee $output

# Finalize benchmark result.

if [ $commit = true ]; then
    module load mysqlpython
    python report-benchmark.py finalize $( grep elapsed $output | awk '{ print $NF }' )
fi
