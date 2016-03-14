#!/bin/bash 
#SBATCH --account=mpccc
#SBATCH --job-name=edison-mpi4py-import-200-tmpfs
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=rcthomas@lbl.gov
#SBATCH --nodes=100
#SBATCH --ntasks-per-node=24
#SBATCH --output=slurm-edison-mpi4py-import-200-tmpfs-%j.out
#SBATCH --partition=debug
#SBATCH --qos=premium
#SBATCH --time=00:15:00

# Load modules.

module swap PrgEnv-intel PrgEnv-gnu
module load python_base
module list

# Verbose debugging output.

set -x

# Stage and activate virtualenv.

envsrc=/usr/common/usg/python/mpi4py-import
envdest=/dev/shm/mpi4py-import/$SLURM_JOBID
envpath=$envdest/mpi4py-import

umask 0000
srun -n $SLURM_JOB_NUM_NODES mkdir -p $envdest
sleep 5
srun -n $SLURM_JOB_NUM_NODES tar cf $envdest/mpi4py-import.tar -C /usr/common/usg/python mpi4py-import 
cd $envdest
srun -n $SLURM_JOB_NUM_NODES tar xf mpi4py-import.tar
cd -
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
    touch $SCRATCH/Edison_Perf/Pynamic/$SLURM_JOB_ID
fi

# Clean-up.

srun -n $SLURM_JOB_NUM_NODES rm -rf $envpath
