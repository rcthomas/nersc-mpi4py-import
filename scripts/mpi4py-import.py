#!/usr/bin/env python

from mpi4py import MPI

comm = MPI.COMM_WORLD
mpi_rank = comm.rank
mpi_size = comm.size
mpi_host = MPI.Get_processor_name()

comm.Barrier()
if mpi_rank == 0 :
    print "mpi4py-import start"

import sys
import time
try :
    import numpy
except :
    print sys.exc_info()[ : 2 ]
    comm.Abort()

# Sometimes it is interesting to see timing here too, but I shut this off by
# default.  If you uncomment this you may also want to unbuffer STDOUT via
# "python -u" or such.

# print "Rank: {:<12}  Size: {:<12}  Host: {:<12}  Time: {:<12}".format( mpi_rank, mpi_size, mpi_host, 
#       time.time() - float( sys.argv[ 1 ] ) )

comm.Barrier()
if mpi_rank == 0 :
    print "mpi4py-import completed     {}".format( time.strftime( "%x %X" ) )
    print "mpi4py-import MPI size      {}".format( mpi_size )
    print "mpi4py-import elapsed (s)   {:.2f}".format( time.time() - float( sys.argv[ 1 ] ) )

comm.Barrier()
