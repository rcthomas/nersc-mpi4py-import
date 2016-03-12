#!/bin/bash -l

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
python setup.py build --mpicc=`which cc`
python setup.py build_exe --mpicc="`which cc` -dynamic"
python setup.py install
cd ..
rm -rf $mpi4py $mpi4py_tgz

# Additional packages via pip.

pip install --no-cache-dir numpy
