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

echo "cleaning up leader"
/competition/cleanup