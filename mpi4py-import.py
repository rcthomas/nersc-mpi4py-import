#!/usr/bin/env python

import sys
import time

from mpi4py import MPI

comm = MPI.COMM_WORLD
mpi_rank = comm.rank
mpi_size = comm.size
mpi_host = MPI.Get_processor_name()
comm.Barrier()

startup_complete = time.time()
startup_elapsed  = startup_complete - float( sys.argv[ 1 ] )

import numpy

print "Rank: {:<12}  Size: {:<12}  Host: {:<12}  Time: {:.2f}".format( mpi_rank, mpi_size, mpi_host, time.time() - startup_complete )
sys.stdout.flush()

comm.Barrier()
import_elapsed = time.time() - startup_complete
if mpi_rank == 0 :
    print "mpi4py-import startup elapsed (s): {:.2f}".format( startup_elapsed )
    print "mpi4py-import  import elapsed (s): {:.2f}".format(  import_elapsed )
    print "mpi4py-import   total elapsed (s): {:.2f}".format( startup_elapsed + import_elapsed )

comm.Barrier()
