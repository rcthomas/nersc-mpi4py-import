#!/usr/bin/env python

import  datetime
import  os

import  matplotlib
matplotlib.use( "Agg" )
import  matplotlib.pyplot as plt
import  MySQLdb
import  numpy as np
import  pandas as pd

DATE_FORMAT = "%Y-%m-%d"
UNIX_EPOCH  = datetime.datetime( 1970, 1, 1 )

def query_by_period_ending( period = 30, ending = None ) :
    ending    = ending or datetime.datetime.utcnow().strftime( DATE_FORMAT )
    end_dt    = datetime.datetime.strptime( ending, DATE_FORMAT )
    begin_dt  = end_dt - datetime.timedelta( days = period )
    end_dt   += datetime.timedelta( days = 1 )
    return query_by_datetime_range( begin_dt, end_dt ), period, ending

def query_by_datetime_range( begin_dt, end_dt ) :
    return query_and_reformat( datetime_range_sql( begin_dt, end_dt ) )

def query_and_reformat( sql ) :
    df = query_raw( sql )
    split_name = df.bench_name.str.split( "-" )
    return df.join( pd.DataFrame( dict( benchmark = split_name.apply( lambda x : "-".join( x[ 1 : -2 ] ) ), 
        setup = split_name.apply( lambda x : x[ -1 ] ) ) ) )

def query_raw( sql ) :
    default_file_path = os.path.join( os.environ[ "HOME" ], ".mysql", ".my_staffdb01.cnf" )
    connection = MySQLdb.connect( db = "benchmarks", read_default_file = default_file_path )
    return pd.read_sql( sql, con = connection )

def datetime_range_sql( begin_dt, end_dt ) :
    return """select bench_name, timestamp, metric_value, jobid, numtasks, hostname from monitor
    where ( bench_name like '%%mpi4py-import%%' or bench_name like '%%pynamic%%' )
    and hostname in ( 'cori', 'edison' ) 
    and notes is null
    and timestamp between {} and {} """.format( timestamp( begin_dt ), timestamp( end_dt ) )

def timestamp( datetime ) :
    return ( datetime - UNIX_EPOCH ).total_seconds()



ylabels = { "mpi4py-import" : "Import Time (s)", 
        "pynamic" : "Start-up + Import + Visit Time (s)" }

titles = { "edison" : u"Edison \u2022 Cray XC30",
        "cori" : u"Cori Data Partition \u2022 Cray XC40" }

suptitles_name = { "mpi4py-import" : "mpi4py-import",
        "pynamic" : "Pynamic v1.3" }

notes = { "mpi4py-import" : "Import numpy from staged relocatable virtualenv. Solid bar is median benchmark time. Lower is better.",
        "pynamic" : "Sum of Pynamic v1.3 start-up, import, and visit only (no compute).  Solid bar is median benchmark time. Lower is better." }

subplots = { "edison" : ( 1, 2, 1 ), 
        "cori" : ( 1, 2, 2 ) }

#

df, period, ending = query_by_period_ending( 60 )
columns = "benchmark numtasks hostname setup metric_value".split()

for ( benchmark, numtasks ), group in df[ columns ].groupby( [ "benchmark", "numtasks" ] ) :

    ymax = 1.1 * group.metric_value.quantile( 0.99 ) 

    for hostname in [ "edison", "cori" ] :

        plt.subplot( *subplots[ hostname ] )

        label_text = list()
        label_xpos = list()
        xpos = 1
        for setup, setup_group in group[ group.hostname == hostname ].groupby( "setup" ) :
            data = setup_group.metric_value
            median = data.median()
            plt.scatter( xpos * np.ones( len( data ) ), data, 30, "red", "x", alpha = 0.2 )
            plt.plot( [ xpos - 0.45, xpos + 0.45 ], [ median, median ], color = "black", lw = 2 )
            plt.text( xpos, median, "{:d} s".format( int( median + 0.5 ) ), ha = "center", va = "bottom" )
            label_text.append( setup )
            label_xpos.append( xpos )
            xpos += 1
        if hostname == "edison" :
            plt.ylabel( ylabels[ benchmark ] )
        else :
            plt.setp( plt.gca().get_yticklabels(), visible = False )
        plt.title( titles[ hostname ], fontsize = 12 )
        plt.gca().set_xticklabels( label_text, rotation = -15, fontsize = 11 )
        plt.gca().set_xticks( label_xpos )
        plt.xlim( 0, xpos )
        plt.ylim( 0, ymax )

    #

    plt.subplots_adjust( wspace = 0.02, hspace = 0 )
    plt.suptitle( u"Benchmark: {} \u2022 {:d} MPI Tasks \u2022 {:d} Days Ending {}".format( 
        suptitles_name[ benchmark ], numtasks, period, ending ) )
    plt.figtext( 0.01, 0.005, notes[ benchmark ], fontsize = 8 )

    # Done.
    
    output_png = "{}-{:d}-{}-{:d}.png".format( ending.replace( "-", "" ), period, benchmark, numtasks )
    plt.savefig( output_png )
    plt.clf()
