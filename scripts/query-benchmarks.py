#!/usr/bin/env python

import  argparse
import  datetime
import  os

import  MySQLdb

parser = argparse.ArgumentParser()
parser.add_argument( "--test",
        help = "test mode", action = "store_true" )
args = parser.parse_args()

fields = "bench_name timestamp jobid numtasks hostname metric_value".split()

query = "select {} from monitor where bench_name like '%%mpi4py-import%';".format( ", ".join( fields ) )

default_file_path = os.path.join( os.environ[ "HOME" ], ".mysql", ".my_staffdb01.cnf" )
connection = MySQLdb.connect( db = "benchmarks", read_default_file = default_file_path )
cursor = connection.cursor()
cursor.execute( query )

for row in cursor :
    results = list()
    for field, column in zip( fields, row ) :
        if field == "bench_name" :
            result = column.split( "-" )[ -1 ]
        elif field == "timestamp" :
            result = str( datetime.datetime.fromtimestamp( column ) )
        else :
            result = column
        results.append( result )
    print "{0:20} {1:20} {2:20} {3:20} {4:20} {5:20}".format( *results )

