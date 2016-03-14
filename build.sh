#!/bin/bash -l

# This script constructs a relocatable virtual environment containing mpi4py
# and numpy.  Here is how to use it.  Type
#
#   ./build.sh
#   ...
#   cp mpi4py-import /usr/common/... (depends on machine)
#   [replace VIRTUAL_ENV in /usr/common/.../mpi4py-import/bin/activate]
#
# It is up to the user to put the virtual environment into the right place on
# whatever the target machine is (/usr/common).

module unload python
module swap PrgEnv-intel PrgEnv-gnu
module load python_base
module load virtualenv
module list

set -x

# Create relocatable virtualenv and activate it.

envname=mpi4py-import

rm -rf $envname
virtualenv --always-copy $envname
virtualenv --relocatable $envname
source $envname/bin/activate

# Install mpi4py into virtualenv.

mpi4py=mpi4py-2.0.0

mpi4py_tgz=$mpi4py.tar.gz
rm -rf $mpi4py $mpi4py_tgz
wget https://bitbucket.org/mpi4py/mpi4py/downloads/$mpi4py_tgz -O $mpi4py_tgz
tar zxvf $mpi4py_tgz
cd $mpi4py

if [ "$NERSC_HOST" = "cori" ]; then
    python setup.py build --mpicc=$(which cc)
    python setup.py build_exe --mpicc="$(which cc) -dynamic"
elif [ "$NERSC_HOST" = "edison" ]; then
    # cancels out the -dynamic...
    LDFLAGS="-shared" python setup.py build --mpicc=$(which cc)
    python setup.py build_exe --mpicc=$(which cc)
else
    echo "Unrecognized NERSC_HOST: $NERSC_HOST"
    exit 137
fi

python setup.py install
cd ..
rm -rf $mpi4py $mpi4py_tgz
 
# Additional packages via pip.
 
pip install --no-cache-dir numpy
