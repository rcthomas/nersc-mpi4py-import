#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=cori-mpi4py-import-150-tmpfs
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=150
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-cori-mpi4py-import-150-tmpfs-%j.out
#SBATCH --partition=regular
#SBATCH --qos=normal
#SBATCH --time=00:10:00

# Load modules.

module swap PrgEnv-intel PrgEnv-gnu
module load python_base
module list

# Verbose debugging output.

set -x

# Stage and activate virtualenv.

envsrc=/usr/common/software/python/mpi4py-import
envdest=/dev/shm/mpi4py-import/$SLURM_JOBID
envpath=$envdest/mpi4py-import

umask 0000
srun -n $SLURM_JOB_NUM_NODES mkdir -p $envdest
sleep 5
srun -n $SLURM_JOB_NUM_NODES cp -r $envsrc $envdest/.
sleep 5
srun -n $SLURM_JOB_NUM_NODES sed -i "s|^VIRTUAL_ENV=.*$|VIRTUAL_ENV=\"$envpath\"|" $envpath/bin/activate
sleep 5
source $envpath/bin/activate
sleep 5

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

# Clean-up.

srun -n $SLURM_JOB_NUM_NODES rm -rf $envpath
