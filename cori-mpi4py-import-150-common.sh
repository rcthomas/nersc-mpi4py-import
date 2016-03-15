#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=cori-mpi4py-import-150-common
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=150
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-cori-mpi4py-import-150-common-%j.out
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

envpath=/usr/common/software/python/mpi4py-import
source $envpath/bin/activate

# Run benchmark.

time srun python mpi4py-import.py $(date +%s)

# Sanity checks.

which python
python -c "import numpy; print numpy.__path__"
strace python -c "import numpy" 2>&1 | grep "open(" | wc

# For usgweb.

if [ "$USER" == "fbench" ]; then
    touch $SCRATCH/Cori_Perf/Pynamic/$SLURM_JOB_ID
fi
