#!/bin/bash

# $1 is hostfile, $2 is formula file
export OMPI_MCA_btl_vader_single_copy_mechanism=none
export RDMAV_FORK_SAFE=1

# ### LOCAL TESTING ###
# mpirun -n 8 --mca btl_tcp_if_include eth0 --allow-run-as-root --hostfile $1 --bind-to none \
#     python3.8 /competition/do_solving.py /competition/cvc5 $2 $1


### AWS TESTING ###
mpirun -n 16 --mca btl_tcp_if_include eth0 --allow-run-as-root --hostfile $1 --bind-to none \
    python3.8 /competition/do_solving.py /competition/cvc5 $2 $1

# ### COMPETITION OFFICIAL ###
# mpirun -n 400 --mca btl_tcp_if_include eth0 --allow-run-as-root --hostfile $1 --bind-to none \
#     python3.8 /competition/do_solving.py /competition/cvc5 $2 $1


# mallob -mono=$2 \
# -zero-only-logging -sleep=1000 -t=4 -appmode=fork -nolog -v=3 -interface-fs=0 -trace-dir=competition \
# -pipe-large-solutions=0 -processes-per-host=$processes_per_host -regular-process-allocation \
# -max-lits-per-thread=50000000 -strict-clause-length-limit=20 -clause-filter-clear-interval=500 \
# -max-lbd-partition-size=2 -export-chunks=20 -clause-buffer-discount=1.0 -satsolver=k

echo "cleaning up leader"
/competition/cleanup