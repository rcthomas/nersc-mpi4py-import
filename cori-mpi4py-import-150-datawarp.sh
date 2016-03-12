#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=cori-mpi4py-import-150-datawarp
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=100
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-cori-mpi4py-import-150-datawarp-%j.out
#SBATCH --partition=debug
#SBATCH --qos=premium
#SBATCH --time=00:15:00
#DW jobdw capacity=2TB access_mode=striped type=scratch

# Load modules.

module swap PrgEnv-intel PrgEnv-gnu
module load python_base
module list

# Verbose debugging output.

set -x

# Stage and activate virtualenv.

envsrc=/usr/common/software/python/mpi4py-import
envdest=$DW_JOB_STRIPED
envpath=$envdest/mpi4py-import

cp -r $envsrc $envdest/.
sed -i "s|^VIRTUAL_ENV=.*$|VIRTUAL_ENV=\"$envpath\"|" $envpath/bin/activate
source $envpath/bin/activate

# Allows up to 5 minutes for pynamic-pyMPI to MPI_Init().

export PMI_MMAP_SYNC_WAIT_TIME=300

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
