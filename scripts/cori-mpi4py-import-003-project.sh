#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --license=project
#SBATCH --job-name=cori-mpi4py-import-003-project
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=3
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-cori-mpi4py-import-003-project-%j.out
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

benchmark_src=/usr/common/software/python/mpi4py-import
benchmark_dest=/project/projectdirs/mpccc/$USER/staged-mpi4py-import/$NERSC_HOST
benchmark_path=$benchmark_dest/mpi4py-import

mkdir -p $benchmark_dest
time rsync -az --exclude "*.pyc" $benchmark_src $benchmark_dest
sed -i "s|^VIRTUAL_ENV=.*$|VIRTUAL_ENV=\"$benchmark_path\"|" $benchmark_path/bin/activate
source $benchmark_path/bin/activate

# Sanity checks, regenerate bytecode.

which python
python -c "import numpy; print numpy.__path__"
strace python -c "import numpy" 2>&1 | grep "open(" | wc

# Initialize benchmark result.

if [ $commit = true ]; then
    module load mysql
    module load mysqlpython
    python report-benchmark.py initialize
    module unload mysqlpython
fi

# Run benchmark.

output=latest-$SLURM_JOB_NAME.txt
time srun python mpi4py-import.py $(date +%s) | tee $output

# Finalize benchmark result.

if [ $commit = true ]; then
    module load mysqlpython
    python report-benchmark.py finalize $( grep elapsed $output | awk '{ print $NF }' )
fi
