#!/usr/bin/env python3.8
import concurrent.futures
import json
import logging
import os
import re
import subprocess
import sys
from mpi4py import MPI
from solver_utils import *
from mpi4py.futures import MPICommExecutor
from collections import defaultdict
import time

# MPI stuff
comm_world = MPI.COMM_WORLD
my_rank = comm_world.Get_rank()
num_procs = comm_world.Get_size()
process_host = MPI.Get_processor_name()
mpi_info = MPI.Info.Create()

def print_data_result(final_result):
    # Going for a json format.
    print("RESULT_DATA {"
          f"\"final_result\" : \"{final_result}\", "
          "} END_RESULT_DATA")
    comm_world.Abort()


# The timeout used for the partitioning itself
partitioning_timeout = 60000

# Solving timeout (total time)
solver_timeout = 1200000
# END OPTIONS

num_scrambles = 134
# num_scrambles = 16
# num_scrambles = 8

num_dedicated_cores = 14
# num_dedicated_cores = 9
# num_dedicated_cores = 6

partitioner = sys.argv[1]
problem_path = sys.argv[2]
host_fl = sys.argv[3]
mpi_info.Set("add-hostfile", host_fl)

size = num_procs

if my_rank == 0:
    leader_ip = socket.gethostbyname(socket.gethostname())
    print("leader ip", leader_ip)
else:
    leader_ip = None
leader_ip = comm_world.bcast(leader_ip, root=0)

def scp_with_retries(ip_addr, temp_file, my_file, max_retries=5, initial_delay=1):
    scp_cmd = f"scp {ip_addr}:{temp_file} {my_file}"

    retries = 0
    while retries <= max_retries:
        print("scp_cmd", scp_cmd, "try number", retries)
        try:
            scp_result = subprocess.run(scp_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
            print(f"(scram workerr) {my_rank} scp command (try {retries}) succeeded with\n",
                    f"stdout: {scp_result.stdout}",
                    f"stderr: {scp_result.stderr}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"(scram worker) {my_rank} scp command (try {retries}) failed with ",
                    f"stdout: {e.stdout}",
                    f"stderr: {e.stderr}")
            retries += 1
            if retries < max_retries:
                sleep_time = initial_delay * (1.5 ** (retries - 1))
                time.sleep(sleep_time)
    return False


def partitioning_leader(pl_my_rank, pl_problem_path, pl_leader_ip, pl_number_of_partitions, pl_strategy, 
                        pl_partitioner_options, pl_rstart):
    print("my rank (partitioning leader)", pl_my_rank, "copying", pl_problem_path, "from", pl_leader_ip)
    my_file = f"/tmp/og_problem{pl_my_rank}.smt2"
    scp_cmd = f"scp {pl_leader_ip}:{pl_problem_path} {my_file}"
    print(f"scp_cmd (partitioning leader) {pl_my_rank}", scp_cmd)

    try:
        scp_result = subprocess.run(scp_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        universal_newlines=True)
        print(f"(partitioning leader) {pl_my_rank} scp command succeeded with\n",
                f"stdout: {scp_result.stdout}",
                f"stderr: {scp_result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"(partitioning leader) {pl_my_rank} scp command failed with ",
                f"stdout: {e.stdout}",
                f"stderr: {e.stderr}")

    print(f"my_file (partitioning leader) {pl_my_rank}", my_file)
    partitioner_options = pl_partitioner_options
    number_of_partitions = pl_number_of_partitions
    checks_before_partition = "1"
    checks_between_partitions = "1"
    strategy = pl_strategy
    partitions = get_partitions(partitioner, partitioner_options, number_of_partitions,
                                my_file, checks_before_partition, checks_between_partitions,
                                strategy, partitioning_timeout)

    print(f"(partitioning leader) {pl_my_rank} partitions {partitions}")
    if partitions in ["sat", "unsat"]:
        print("sat or unsat, we solved it")
        print_data_result(partitions)
    if partitions in ["timeout", "error", "unknown"]:
        print(f"something bad happened {pl_my_rank} - ", partitions)
    if not partitions in ["timeout", "error", "unknown"]:
        rstart = num_dedicated_cores + num_scrambles + pl_rstart
        rend = rstart + len(partitions)
        for i, partition in enumerate(partitions, start=rstart):
            print("sending a partition to i = ", i)
            comm_world.send((partition, "no_ip_needed", pl_my_rank), dest=i)
        # Post all receive requests
        requests = [comm_world.irecv(source=i) for i in range(rstart, rend)]

        results = [None] * len(requests)  # Placeholder for results
        finished = [False] * len(requests)  # Keep track of which requests have finished

        while not all(finished):  # While there's still outstanding requests
            for i, req in enumerate(requests):
                if not finished[i]:  # If this request hasn't finished yet
                    result = req.test()
                    if result[0]:  # If the request has completed
                        results[i] = result[1]  # Store the result
                        finished[i] = True  # Mark as finished
                        
                        # If the result is "sat", print and abort
                        if results[i] == "sat":
                            print_data_result("sat")
                            comm_world.Abort()
                            
        # If all results are "unsat", print and abort
        if all(result == "unsat" for result in results) and len(results) > 0:
            print_data_result("unsat")
            comm_world.Abort()


if my_rank == 0 or my_rank == 1:  # Leader scramblers
    Sn = num_scrambles // 2  # Divide by 2 for the two sets of scrambles
    start = num_dedicated_cores + Sn * my_rank  # Determine the starting worker node for each leader node
    for i in range(start, start + Sn):
        print("scram rank", my_rank, "sending scramble to i=", i)
        temp_file, ip_addr = get_scrambles(problem_path, i)
        comm_world.send((temp_file, ip_addr, my_rank), dest=i)

elif my_rank == 2:  # Leader Node  3
    partitioning_leader(my_rank, problem_path, leader_ip, 2, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        0)

elif my_rank == 3:  # Leader Node  4
    partitioning_leader(my_rank, problem_path, leader_ip, 2, "decision-dncs", 
        " --partition-when tlimit --partition-start-time 3 --partition-time-interval 0.1 --partition-tlimit 45 ",
        2)
    
elif my_rank == 4:  # Leader Node  5
   partitioning_leader(my_rank, problem_path, leader_ip, 4, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ",
        2 + 2)
elif my_rank == 5:  # Leader Node  6
    partitioning_leader(my_rank, problem_path, leader_ip, 4, "decision-dncs", 
        " --partition-when tlimit --partition-start-time 3 --partition-time-interval 0.1 --partition-tlimit 45 ",
        2 + 2 + 4)

elif my_rank == 6:  # Leader Node  7
    partitioning_leader(my_rank, problem_path, leader_ip, 8, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4)
   
elif my_rank == 7:  # Leader Node  8
    partitioning_leader(my_rank, problem_path, leader_ip, 8, "decision-dncs", 
        " --partition-when tlimit --partition-start-time 3 --partition-time-interval 0.1 --partition-tlimit 45 ",
        2 + 2 + 4 + 4 + 8)

elif my_rank == 8:  # Leader Node  9
    partitioning_leader(my_rank, problem_path, leader_ip, 16, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8)

elif my_rank == 9:  # Leader Node  10
    partitioning_leader(my_rank, problem_path, leader_ip, 16, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8 + 16)

elif my_rank == 10:  # Leader Node  11
    partitioning_leader(my_rank, problem_path, leader_ip, 32, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8 + 16 + 16)

elif my_rank == 11:  # Leader Node  12
    partitioning_leader(my_rank, problem_path, leader_ip, 32, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8 + 16 + 16 + 32)

elif my_rank == 12:  # Leader Node  13
    partitioning_leader(my_rank, problem_path, leader_ip, 64, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8 + 16 + 16 + 32 + 32)

elif my_rank == 13:  # Leader Node  14
    partitioning_leader(my_rank, problem_path, leader_ip, 64, "decision-cubes", 
        " --partition-when tlimit --partition-tlimit 10 --partition-start-time 3  ", 
        2 + 2 + 4 + 4 + 8 + 8 + 16 + 16 + 32 + 32 + 64)

else:  # Worker nodes

    received, ip_addr, p_rank = comm_world.recv(source=MPI.ANY_SOURCE)
    if my_rank < num_dedicated_cores + num_scrambles:  # Worker nodes dealing with scrambles
        temp_file = received  # In this case, the received data is a temp file
        print("my rank (scram worker)", my_rank, "copying", temp_file, "from", ip_addr)
        my_file = f"/tmp/{os.path.basename(temp_file)}{my_rank}.smt2"
        scp_with_retries(ip_addr, temp_file, my_file, max_retries=5, initial_delay=1)
        # scp_cmd = f"scp {ip_addr}:{temp_file} {my_file}"
        # print("scp_cmd", scp_cmd)
        # try:
        #     scp_result = subprocess.run(scp_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        #                     universal_newlines=True)
        #     print(f"(scram workerr) {my_rank} scp command succeeded with\n",
        #             f"stdout: {scp_result.stdout}",
        #             f"stderr: {scp_result.stderr}")
        # except subprocess.CalledProcessError as e:
        #     print(f"(scram worker) {my_rank} scp command failed with ",
        #             f"stdout: {e.stdout}",
        #             f"stderr: {e.stderr}")
        print(f" (scram worker {my_rank}) my_file", my_file)
        smt_comp_solver_script = "/competition/run-script-smtcomp-current" 
        timeout = 1200000
        result = run_solver(smt_comp_solver_script, my_file, timeout)
        print("scram result", result)
        if result in ["sat", "unsat"]:
            print_data_result(result)
            comm_world.Abort()
    else:  # Worker nodes dealing with partitions
        partition = received  # In this case, the received data is a partition string
        print("my rank (partitioning worker)", my_rank, "copying", problem_path, "from", leader_ip)
        my_file = f"/tmp/og_problem{my_rank}.smt2"
        scp_with_retries(ip_addr, problem_path, my_file, max_retries=5, initial_delay=1)
        # scp_cmd = f"scp {leader_ip}:{problem_path} {my_file}"
        # print("scp_cmd", scp_cmd)
        # subprocess.run(scp_cmd, shell=True)
        print(f" (part worker {my_rank}) my_file", my_file)
        my_partition = stitch_partition(partition, my_file)  # Stitch the partition string to the original file
        smt_comp_solver_script = "/competition/run-script-smtcomp-current" 
        timeout = 1200000
        result = run_solver(smt_comp_solver_script, my_partition, timeout)
        print("partition result", result)
        comm_world.send(result, dest=p_rank)

