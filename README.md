
Benchmark mpi4py-import on Edison and Cori
==========================================

This document describes the deployment and operation of the mpi4py-import benchmark on the Edison and Cori systems at NERSC.

The mpi4py-import benchmark measures realistic typical Python import performance at scale.
It does this by trying to import a test package suite containing packages that users commonly use.
Right now this consists of `numpy` and `astropy` (added 2016-05-11) but the suite could be expanded if needed.
The idea is to use a package or packages with several thousand file metadata operations to provide an indicator that users can reference to gauge how long they
    can expect typical imports to take at scale.
The benchmark is not exhaustive by any means, but is easy to understand and seems to test things more meaningful to users than Pynamic does.
Pynamic is very useful for the center to run, but not terribly informative to users directly.
Interestingly good performance on one benchmark does not necessarily predict good performance on the other, and vice versa.

Configuration
-------------

We construct a "relocatable" Python virtual environment (virtualenv) containing mpi4py and the test package suite.
The first step is simply initializing the virtualenv with the "--always-copy" option to copy Python system files instead of symlinking them in.
The virtualenv is made "relocatable" by re-running virtualenv with the "--relocatable" flag.
According to the documentation, this "fixes up scripts and makes all .pth files relative."
However it does not change the `activate` script which is necessary once the virtualenv has actually been relocated, as described below under Execution.

The mpi4py package is installed into the virtualenv following standard NERSC procedure using the Cray compiler wrappers.
The details depend on the machine and exactly how Python was built on the host.
Finally the test package suite is installed via pip.

All of the above steps, including the download and installation of mpi4py, are contained in the script build-virtualenv.sh.
On either machine we copy the new virtualenv (called mpi4py-import) to the global common filesystem.  Specifically:

    edison: /usr/common/usg/python/mpi4py-import
    cori:   /usr/common/software/python/mpi4py-import

Execution
---------

Batch job scripts for small (100 core) and large (4800 core) runs have been created for either machine to run mpi4py-import within the following test matrix.

|        | common | datawarp | project | scratch | shifter | tmpfs |
| ------ |:------:|:--------:|:-------:|:-------:|:-------:|:-----:|
| Edison | yes    | N/A      | yes     | yes     | no      | yes   |
| Cori   | yes    | yes      | yes     | yes     | no      | yes   |

The general sequence of events for a benchmark job is basically the same in all cases.
The environment is first initialized, but only the python_base module is loaded.
If run with the `debug` variable set to true, the loaded modules are listed and trace output is enabled (`set -x`).
If the benchmark run is on the the global common filesystem, we simply activate the virtualenv.
In other cases, we stage the virtualenv to the target filesystem, update the `activate` script, and then activate the virtualenv.

Staging the virtualenv every time the benchmark runs is unnecessarilyl time-consuming.
We use `rsync -az` so that if a previous benchmark run has already staged the virtualenv we do not repeat the process.
Using the `--exclude "*.pyc"` option prevents staging compiled bytecode files to the target system.
Modifying the `activate` script is just an update of a single line defining `$VIRTUAL_ENV` to be the target directory.

A few commands are run to help indicate whether the setup is correct, including the path to the Python interpreter.
At least one module from the test suite is imported and its path is also output.
Another execution of the import is run to quantify the number of open() calls using `strace.`

These executions are done from a single process.
This step was introduced and placed before the actual benchmark run because there seemed to be contention creating bytecode files when the benchmark would run.
Putting these in place first through a single process execution first seemed to resolve the problem.
There are other methods of preventing creation of bytecode files altogether.

Next a benchmark result spot is reserved in the database if this result is being cached there.
This is done using a Python script with its own depenedencies (database client API) which we unload before launching the benchmark.
This controls the length of `PYTHONPATH`.

The benchmark is then run at full scale and the result (elapsed time for all MPI ranks to complete import) is captured.
This result is then stored in the database.
If the benchmark starts but fails to produce usable output, or hangs until the wall-clock expires, then the original placeholder `NULL` value remains unchanged.

Management
----------

These benchmarks are managed via `crontab` on both machines.
The idea is that a small mpi4py-import job is selected to run every 6 hours or so.
A larger mpi4py-import job is selected to run once a day or so.
The exact benchmark selected is chosen randomly.
This random selection plus the queue wait times help us eventually converge to good sampling as a function of time of day.
