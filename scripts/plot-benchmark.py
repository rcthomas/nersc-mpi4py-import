#!/usr/bin/env python

import  argparse
import  datetime
import  os
import  sys

import  matplotlib
matplotlib.use( "Agg" )

import  matplotlib.pyplot as plt
import  MySQLdb
import  numpy as np
import  pandas as pd


DATE_FORMAT = "%Y-%m-%d"
UNIX_EPOCH  = datetime.datetime( 1970, 1, 1 )

ylabels = { "mpi4py-import" : "Import Time (s)", 
        "pynamic" : "Start-up + Import + Visit Time (s)" }

titles = { "edison" : u"Edison \u2022 Cray XC30",
        "cori" : u"Cori Data Partition \u2022 Cray XC40" }

suptitles_name = { "mpi4py-import" : "mpi4py-import",
        "pynamic" : "Pynamic v1.3" }

notes = { "mpi4py-import" : "Import numpy from virtualenv. Solid bar is median benchmark time.",
        "pynamic" : "Pynamic v1.3 start-up + import + visit only (no compute).  Solid bar is median benchmark time." }

subplots = { "edison" : ( 1, 2, 1 ), 
        "cori" : ( 1, 2, 2 ) }


def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument( "--period", help = "length of sampling period (days) [%(default)s]", default = 60 )
    parser.add_argument( "--ending", help = "sampling period UTC end date YYYY-MM-DD [today]" )
    return generate_figures( parser.parse_args() )


def generate_figures( args ) :
    df, period, ending = query_by_period_ending( args.period, args.ending )
    for ( benchmark, numtasks ), group in df.groupby( [ "benchmark", "numtasks" ] ) :
        suptitle = suptitles_name[ benchmark ]
        note = notes[ benchmark ]
        generate_figure( benchmark, numtasks, group, period, ending, suptitle, note )


def generate_figure( benchmark, numtasks, group, period, ending, suptitle, note ) :

    ymax = 1.1 * group.metric_value.quantile( 0.99 )

    for hostname in [ "edison", "cori" ] :
        axes = plt.subplot( *subplots[ hostname ] )
        setup_groups = group[ group.hostname == hostname ].groupby( "setup" )
        title = titles[ hostname ]
        ylabel = ylabels[ benchmark ] if hostname == "edison" else None
        generate_plot( axes, setup_groups, title, ymax, ylabel )

    plt.subplots_adjust( wspace = 0.02, hspace = 0 )
    plt.suptitle( u"Benchmark: {} \u2022 {:d} MPI Tasks \u2022 {:d} Days Ending {}".format( suptitle, numtasks, period, 
        ending ) )
    plt.figtext( 0.01, 0.005, note, fontsize = 8 )
    
    output_png = "{}-{:d}-{}-{:d}.png".format( ending.replace( "-", "" ), period, benchmark, numtasks )
    plt.savefig( output_png )
    plt.clf()


def generate_plot( axes, setup_groups, title, ymax, ylabel = None ) :

    tick_text = list()
    tick_pos  = list()
    curr_pos  = 1

    for setup, group in setup_groups :

        data = group.metric_value
        x = curr_pos * np.ones_like( data )
        median = data.median()

        axes.scatter( x, data, 30, "red", "x", alpha = 0.2 )
        axes.plot( [ curr_pos - 0.45, curr_pos + 0.45 ], [ median, median ], color = "black", lw = 2 )
        axes.text( curr_pos, median, "{:d} s".format( int( median + 0.5 ) ), ha = "center", va = "bottom" )

        tick_text.append( setup )
        tick_pos.append( curr_pos )
        curr_pos += 1

    format_title( axes, title )
    format_x_axis( axes, curr_pos, tick_text, tick_pos )
    format_y_axis( axes, ymax, ylabel )


def format_title( axes, title ) :
    axes.set_title( title, fontsize = 12 )


def format_x_axis( axes, limit, tick_text, tick_pos ) :
    axes.set_xlim( 0, limit )
    axes.set_xticklabels( tick_text, rotation = -15, fontsize = 11 )
    axes.set_xticks( tick_pos )


def format_y_axis( axes, limit, label_text ) :
    axes.set_ylim( 0, limit )
    if label_text is None :
        axes.set_yticklabels( [], visible = False )
    else :
        axes.set_ylabel( label_text )


def query_by_period_ending( period, ending ) :
    ending    = ending or datetime.datetime.utcnow().strftime( DATE_FORMAT )
    end_dt    = datetime.datetime.strptime( ending, DATE_FORMAT )
    begin_dt  = end_dt - datetime.timedelta( days = period )
    end_dt   += datetime.timedelta( days = 1 )
    return query_by_datetime_range( begin_dt, end_dt ), period, ending


def query_by_datetime_range( begin_dt, end_dt ) :
    return query_and_format( datetime_range_sql( begin_dt, end_dt ) )


def query_and_format( sql ) :
    df = query_raw( sql )
    split_name = df.bench_name.str.split( "-" )
    df = df.join( pd.DataFrame( dict( benchmark = split_name.apply( lambda x : "-".join( x[ 1 : -2 ] ) ), 
        setup = split_name.apply( lambda x : x[ -1 ] ) ) ) )
    return df[ "benchmark numtasks hostname setup metric_value".split() ]


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


if __name__ == "__main__" :
    sys.exit( main() )
