#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=edison-mpi4py-import-200-common
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=200
#SBATCH --ntasks-per-node=24
#SBATCH --output=slurm-edison-mpi4py-import-200-common-%j.out
#SBATCH --partition=regular
#SBATCH --qos=low
#SBATCH --time=00:10:00

# Load modules.

module swap PrgEnv-intel PrgEnv-gnu
module load python_base
module list

# Verbose debugging output.

set -x

# Stage and activate virtualenv.

envpath=/usr/common/usg/python/mpi4py-import
source $envpath/bin/activate

# Run benchmark.

time srun python mpi4py-import.py $(date +%s)

# Sanity checks.

which python
python -c "import numpy; print numpy.__path__"
strace python -c "import numpy" 2>&1 | grep "open(" | wc

# For usgweb.

if [ "$USER" == "fbench" ]; then
    touch $SCRATCH/Edison_Perf/Pynamic/$SLURM_JOB_ID
fi
