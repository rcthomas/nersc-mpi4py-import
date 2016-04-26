#!/usr/bin/env python

"""Create or update benchmark results in a NERSC benchmark database.

Use this program to record benchmark results in a database at NERSC for report
generation later.  There are two modes of execution.  These are single-step
"insert" mode and two-phase "initialize/finalize" mode.

Insert mode allows you to record a benchmark result in the database through a
single invocation.  This should be needed rarely but having a way to manually 
insert benchmark results is handy in special cases.

Two-phase initialize/finalize mode lets you first reserve a placeholder result
slot in the database that you subsequently update with the benchmark outcome.
This should be the main usage mode.  You should only use this mode from within
a benchmark batch job though.  Invocation in that case is simple because many
required entries like job ID, system, or timestamp are included automatically.
Here is how the two-phase mode works.  

[1] First an initializing invocation is made that records a NULL value for the
benchmark result indicating approximately when the benchmark was launched.

[2] Ideally the benchmark application runs successfully and a result is
extracted, probably from the benchmark's standard output stream.  To finalize
the benchmark entry this result is used to replace the original NULL value
recorded in the initialization phase.

The benchmark may fail to execute for some reason.  It may start up but then
crash at a point before a reportable result is extracted from its output.  Most
importantly, the benchmark may evan fail to reach such a point before the
requested job time limit is reached.  If any such problems occur the finalize
step will fail or simply not be executed.  Such failures are represented in the
database by the unmodified NULL value.  This logic obviously does not apply to
benchmarks underway at any given time.

Example:
    To simply insert a benchmark result in one go, use the "insert" command and
    provide the required positional arguments (1) benchmark name, (2) unix
    timestamp of the result, (3) job ID, (4) number of tasks, (5) host or
    system name, and (6) the metric value itself such as the time in seconds
    (default).  For instance::

        $ python report-benchmark.py insert 
            name-of-my-benchmark 1460590909 134151 4800 cori 13.32

    Not sure that you have everything set up properly?  Don't worry, you can 
    prepend the "--test" argument before the command (insert) to see what would
    happen.  For example, changing the above command we would see::

        $ python report-benchmark.py --test insert 
            name-of-my-benchmark 1460590909 134151 4800 cori 13.32
        insert into monitor ( bench_name, timestamp, jobid, numtasks, hostname, 
            metric_value, metric_units, apid ) values ( 'name-of-my-benchmark', 
            1460590909, '134151', 4800, 'cori', 13.32, 'seconds', 0 )
        *** TEST MODE *** 

    Note the "--test" argument needs to come before the "insert."

Example:
    A two-phase initialize/finalize report is carried out in the following way.
    The initialize step is just::

        python report-benchmark.py initialize

    Then the benchmark runs.  Suppose you extract a result and store it in a
    shell variable called "$result."  Finalize the benchmark record with this
    value like so::

        python report-benchmark.py finalize $result

    This pair of commands bracketing the benchmark use job environment variables
    to do the right thing, making invocations much simpler than the single-shot 
    mode where we depend entirely on the user for filling in all the report 
    columns.
"""


import  argparse
import  os
import  sys
import  time

import  MySQLdb


def from_environ( name, test = False ) :
    """Return environment variable if defined (placeholder in test mode)."""
    return "${}".format( name ) if test else os.environ[ name ]


class Command ( object ) :
    """Represents an executable SQL command."""

    @property
    def sql( self ) :
        """SQL command representation."""
        try :
            return self._sql
        except AttributeError :
            self._sql = self._define_sql()
            return self._sql

    def _define_sql( self ) :
        """Implement SQL command representation."""
        raise NotImplementedError


class Insert ( Command ) :
    """Insertion of benchmark result or a placeholder result."""

    @classmethod
    def within_job( cls, test = False ) :
        """Construct placeholder benchmark insert using job environment information."""
        bench_name = from_environ( "SLURM_JOB_NAME", test )
        timestamp  = int( time.time() )
        jobid      = from_environ( "SLURM_JOB_ID", test )
        numtasks   = from_environ( "SLURM_NTASKS", test )
        hostname   = from_environ( "NERSC_HOST", test )
        return cls( bench_name, timestamp, jobid, numtasks, hostname, "NULL" )

    def __init__( self, bench_name, timestamp, jobid, numtasks, hostname, metric_value, metric_units = "seconds", 
            apid = 0 ) :
        self.bench_name   = bench_name
        self.timestamp    = timestamp
        self.jobid        = jobid
        self.numtasks     = numtasks
        self.hostname     = hostname
        self.metric_value = metric_value
        self.metric_units = metric_units
        self.apid         = apid

    def _define_sql( self ) :
        text  = "insert into monitor "
        text += "( bench_name, timestamp, jobid, numtasks, hostname, metric_value, metric_units, apid ) "
        text += "values ( "
        text += "'{}', ".format( str( self.bench_name ) )
        text += "{}, ".format( str( self.timestamp ) )
        text += "'{}', ".format( str( self.jobid ) )
        text += "{}, ".format( str( self.numtasks ) )
        text += "'{}', ".format( str( self.hostname ) )
        text += "{}, ".format( str( self.metric_value ) )
        text += "'{}', ".format( str( self.metric_units ) )
        text += "{} )".format( str( self.apid ) )
        return text


class Update ( Command ) :
    """Update of existing benchmark result."""

    @classmethod
    def within_job( cls, metric_value, test = False ) :
        """Construct benchmark update using job information."""
        jobid = from_environ( "SLURM_JOB_ID", test )
        return cls( jobid, metric_value )

    def __init__( self, jobid, metric_value ) :
        self.jobid        = jobid
        self.metric_value = metric_value

    def _define_sql( self ) :
        return "update monitor set metric_value={} where jobid='{}'".format( self.metric_value, self.jobid )


def insert( args ) :
    """Insert fully-defined benchmark result (use this for backfill)."""
    return Insert( args.bench_name, args.timestamp, args.jobid, args.numtasks, args.hostname, args.metric_value )


def initialize( args ) :
    """Initialize benchmark result with a placeholder."""
    return Insert.within_job( args.test )


def finalize( args ) :
    """Finalize benchmark result with a metric value."""
    return Update.within_job( args.metric_value, args.test )


def parse_arguments() :
    """Parse command line arguments and return them."""

    # Parser with global options and some sub-commands.

    parser = argparse.ArgumentParser( description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter )
    parser.add_argument( "--test"         , help = "activate test mode"  , action = "store_true" )
    parser.add_argument( "--verbose", "-v", help = "more detailed output", action = "store_true" )
    subparsers = parser.add_subparsers()

    # Insert sub-command with all positional arguments.

    insert_parser = subparsers.add_parser( "insert" )
    insert_parser.add_argument( "bench_name"  , help = "benchmark name"                         )
    insert_parser.add_argument( "timestamp"   , help = "seconds since Unix epoch", type = int   )
    insert_parser.add_argument( "jobid"       , help = "batch job identifier"                   )
    insert_parser.add_argument( "numtasks"    , help = "number of tasks"         , type = int   )
    insert_parser.add_argument( "hostname"    , help = "hostname/system"                        )
    insert_parser.add_argument( "metric_value", help = "metric value"            , type = float )
    insert_parser.set_defaults( func = insert )

    # Initialize sub-command where context provides everything.

    init_parser = subparsers.add_parser( "initialize" )
    init_parser.set_defaults( func = initialize )

    # Finalize sub-command that just takes the metric value.

    final_parser = subparsers.add_parser( "finalize" )
    final_parser.add_argument( "metric_value", help = "metric value", type = float )
    final_parser.set_defaults( func = finalize )

    # Parse args, set verbose if test mode, return.

    args = parser.parse_args()
    if args.test :
        args.verbose = True
    return args


def broker_connection( default_file_path = None, db = "benchmarks" ) :
    """Set up database connection."""

    if default_file_path is None :
        default_file_path = os.path.join( os.environ[ "HOME" ], ".mysql", ".my_staffdb01.cnf" )

    return MySQLdb.connect( db = db, read_default_file = default_file_path )


def main() :

    args = parse_arguments()
    cmd  = args.func( args )

    if args.verbose :
        print cmd.sql

    if args.test :
        print "*** TEST MODE ***"
        return

    connection = broker_connection()
    cursor     = connection.cursor()
    result     = cursor.execute( cmd.sql )

    if args.verbose :
        print result


if __name__ == "__main__" :
    main()
