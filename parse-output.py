#!/usr/bin/env python

import  datetime
import  sys

class Mpi4pyImportRun ( object ) :

    def __init__( self, output_path ) :
        self.output_path = output_path
        self._parse_output_path()
        self._parse_output_content()

    def _parse_output_path( self ) :
        tokens = self.output_path[ : -4 ].split( "-" )
        self.host   = tokens[ 1 ]
        self.setup  = "-".join( tokens[ 5 : -1 ] )
        self.job_id = int( tokens[ -1 ] )

    def _parse_output_content( self ) :
        time = list()
        for line in self._output_content() :
            if line.startswith( "mpi4py-import completed" ) :
                date, time = line.split()[ -2 : ]
            if line.startswith( "mpi4py-import MPI size" ) :
                size = line.split()[ -1 ]
            if line.startswith( "mpi4py-import elapsed" ) :
                elapsed_time = float( line.split()[ -1 ] )
        self.executed     = datetime.datetime.strptime( " ".join( [ date, time ] ), "%x %X" )
        self.mpi_size     = int( size )
        self.elapsed_time = elapsed_time

    def _output_content( self ) :
        with open( self.output_path, "r" ) as stream :
            return list( stream )

    def __repr__( self ) :
        result = "{:<10} {:<15} {:<10} {:<20} {:<5} {:8.2f}".format( self.host, self.setup, self.job_id,
                self.executed.isoformat(), self.mpi_size, self.elapsed_time )
        if self.executed.date() == datetime.date.today() :
            result = "\033[1m" + result + "\033[0m"
        return result

    def __cmp__( self, other ) :
        if self.host < other.host :
            return -1 
        if self.host > other.host :
            return +1
        if self.setup < other.setup :
            return -1
        if self.setup > other.setup :
            return +1
        if self.executed < other.executed :
            return -1
        if self.executed > other.executed :
            return +1
        return 0

if __name__ == "__main__" :

    import argparse
    import os
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument( "output_paths", help = "list of output paths to parse", nargs  = "+" )
    args = parser.parse_args()

    runs = list()
    for path in args.output_paths :
        try :
            runs.append( Mpi4pyImportRun( path ) )
        except :
            cdate = datetime.date.fromtimestamp( os.path.getctime( path ) )
            message = "[WARNING] Unable to parse {} (created {})".format( path, cdate.isoformat() )
            if cdate == datetime.date.today() :
                message = "\033[1m\033[91m" + message + "\033[0m\033[0m"
            sys.stderr.write( "{}\n".format( message ) )
            pass

    for run in sorted( runs ) :
        print run
