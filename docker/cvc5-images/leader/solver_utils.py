import subprocess
import os
import json
import boto3
import requests
import re
from pathlib import Path
import tempfile
import socket


scrambler_seed = [
1610, 61549, 14733, 51490, 18463, 5672, 18179, 14739, 30383, 18297, 19321, 4341, 7946, 17902, 30300, 58688, 54077, 26861, 12205, 15486, 2670, 
52815, 44766, 26018, 26992, 43295, 51373, 47828, 32318, 27569, 28433, 54571, 7872, 6759, 23579, 46597, 17661, 26721, 19350, 49338, 3981, 
11287, 57499, 28621, 27229, 56675, 48166, 25404, 43339, 28729, 63190, 5429, 34524, 44042, 38454, 43823, 51927, 63154, 41469, 27939, 12493, 
40150, 23108, 38677, 12259, 22752, 25270, 3770, 49117, 12537, 52321, 37332, 40053, 25808, 14942, 59612, 26556, 43770, 58285, 52814, 6361, 
15472, 35087, 12959, 15640, 25443, 26360, 43938, 21280, 19907, 62350, 7597, 65294, 36439, 48812, 64259, 4991, 14683, 63626, 18079, 65230, 
3223, 33392, 64194, 61588, 45705, 31122, 1467, 12685, 49177, 37031, 58438, 23084, 5911, 17321, 16365, 6553, 27068, 25339, 39155, 24095, 
59619, 52613, 29746, 25511, 60496, 40433, 61198, 42724, 17516, 48703, 16185, 45464, 25107, 38366, 49718, 21781, 5507, 15573, 55690, 27219, 
18433, 32180, 49900, 40265, 26848, 55774, 40235, 31818, 35318, 4955, 4323, 61902, 35925, 33926, 26498, 57000, 47695, 27600, 52597, 4376, 
58142, 50352, 26011, 31458, 28100, 42206, 45301, 38933, 48268, 14722, 28313, 8646, 32642, 62853, 65517, 59236, 36354, 23799, 54760, 4424, 
8917, 63240, 20187, 38948, 62100, 732, 27, 36338, 49766, 35715, 37258, 39382, 32250, 40301, 52881, 30566, 31332, 18672, 41908, 12583, 
24588, 2703, 48917, 64546, 40116, 61470, 34039, 40450, 50810, 52167, 27982, 29049, 53832, 6329, 31760, 31377, 6309, 53905, 42430, 35775, 
14149, 8085, 42963, 32544, 64448, 56047, 18441, 6248, 40507, 40977, 5874, 53598, 29541, 57729, 18531, 10048, 3036, 64683, 62043, 57676, 
35620, 62921, 62660, 445, 44417, 30822, 22120, 11766, 60977, 47049, 7457, 51375, 42239, 51006, 26502, 54787, 28709, 7603, 58482, 5091, 
54020, 59110, 52623, 17818, 41762, 56116, 31380, 33761, 11917, 59453, 7320, 17994, 40203, 25712, 16406, 49950, 61384, 29961, 36033, 44697, 
44658, 55193, 41053, 35725, 57720, 55078, 44900, 9063, 24415, 29636, 34071, 22209, 15253, 14181, 40664, 34864, 59043, 56637, 25775, 10252, 
12387, 43739, 63701, 62492, 46164, 18779, 57160, 63222, 20417, 8129, 33504, 42142, 41113, 40373, 7747, 42563, 15753, 29914, 23320, 34575, 
18380, 39871, 50987, 57856, 41655, 33947, 9807, 22048, 19462, 18735, 62206, 18654, 55822, 59425, 23649, 22586, 60354, 17467, 46625, 51019, 
63956, 26163, 63184, 44043, 1721, 65535, 48740, 24621, 17851, 63345, 40364, 21246, 27137, 12526, 60452, 65095, 45329, 17587, 9318, 37925, 
22098, 8527, 12852, 2465, 6754, 45583, 23591, 31185, 9604, 48562, 54265, 54418, 39039, 6809, 39021, 52437, 12885, 8535, 12668, 52950, 
21447, 38569, 21212, 4778, 45101, 9731, 18851, 51831, 37694, 13246, 42655, 32126, 32693, 61917, 47059, 54140, 56021, 21711, 34489, 1795]

def get_input_json(request_directory):
    # print("solver_utils get_input json")
    inp = os.path.join(request_directory, "input.json")
    with open(inp) as f:
        return json.loads(f.read())


"""
Make partitions by executing the partitioner with the provided options. 

  partitioner : the executable to use for partitioning
  partitioner_options : extra cli arguments to pass to partitioner
  number_of_partitions : The desired number of partitions to be made. 
  output_file : The file that partitions are written to. 
  smt_file : The full path of the smt2 benchmark file being partitioned.
  checks_before_partition : number of checks before partitioner starts 
                            making partitions
  checks_between_partitions : number of checks between subsequent partitions
  strategy : the partitioning strategy to send to the partitioner
  debug : flag that indicates whether debug information should be printed
  returns : void

TODO: Probably want to check for errors and/or confirm that the 
partitions were actually made and return something like a bool.
"""


def make_partitions(partitioner, partitioner_options, number_of_partitions,
                    smt_file, checks_before_partition, checks_between_partitions,
                    strategy, time_limit):

    # print("Making partitons")
    # Build the partition command
    partition_command = (
        f"{partitioner} --compute-partitions={number_of_partitions} "
        f" --tlimit={time_limit} "
        f"--lang=smt2 --partition-strategy={strategy} "
        f"--checks-before-partition={checks_before_partition} "
        f"--checks-between-partitions={checks_between_partitions} "
        f"{partitioner_options} {smt_file}"
    )

    try:
        output = subprocess.check_output(
            partition_command, shell=True, stderr=subprocess.STDOUT)
        # print("partitioning at least terminated")
        partitions = output.decode("utf-8").strip().split('\n')

        # print("partitions", partitions)

        # Handle case where problem is solved while partitioning.
        if partitions[-1] == "sat":
            return "sat"
        elif len(partitions) == 1 and partitions[-1] == "unsat":
            return "unsat"
        elif len(partitions) == 1 and partitions[-1] == "unknown":
            return "unknown"
        # If not solved, then return the partitions
        else:
            return partitions[0: len(partitions) - 1]
    except Exception as e:
        # If the partitioning timed out, good to know.
        if "timeout" in str(e.output):
            # print("timout")
            return "timeout"
        # Any other error is just an error.
        else:
            print(e)
            return "error"
            


def get_partitions(partitioner, partitioner_options, number_of_partitions,
                   smt_file, checks_before_partition, checks_between_partitions,
                   strategy, time_limit):

    partitions = make_partitions(partitioner, partitioner_options, number_of_partitions,
                                 smt_file, checks_before_partition, checks_between_partitions,
                                 strategy, time_limit)

    return partitions


"""
Make a copy of the partitioned problem and append a cube to it for each cube
that is in the list of partitions.
  partitions : The list of cubes to be appended to copies of the partitioned
               problem. 
  stitched_directory : The directory in which the stitched files will be 
                       written.  
  parent_file : The file that was partitioned. 
  debug : flag that indicates whether debug information should be printed
  returns : void
"""


def stitch_partition(partition, parent_file):
    # print("PARTITION INFO : " + partition)

    # Read the original contents in
    with open(parent_file) as bench_file:
        bench_contents = bench_file.readlines()

        # Append the cube to the contents before check-sat
        check_sat_index = bench_contents.index("(check-sat)\n")
        bench_contents[check_sat_index:check_sat_index] = \
            f"(assert {partition})\n"
    with tempfile.NamedTemporaryFile(delete=False) as new_bench_file:
        new_bench_file.write("".join(bench_contents).encode('utf-8'))
        return new_bench_file.name

def get_instance_id():
    response = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
    return response.text

def get_private_ip(instance_id):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)
    return instance.private_ip_address

def get_scrambles(smt_file, idx):
    # print("get_scrambles", smt_file, idx)
    #prefix = os.path.dirname(smt_file)
    my_ip = socket.gethostbyname(socket.gethostname())
    if idx == 10: # the first one
        with tempfile.NamedTemporaryFile(delete=False) as scramble_file: 
            cp_cmd = f"cp {smt_file} {scramble_file.name}"
            # print("null scramble cp_cmd", cp_cmd)
            subprocess.run(cp_cmd, shell=True) 
            return scramble_file.name, my_ip
    else:
        seed = scrambler_seed[idx]
        with tempfile.NamedTemporaryFile(delete=False) as scramble_file:
            scram_cmd = f"/competition/scrambler  -seed {seed} < {smt_file} > {scramble_file.name}" 
            # print("scram_cmd", scram_cmd)
            subprocess.run(scram_cmd, shell=True) 
            return scramble_file.name, my_ip

def make_scrambles(num_scrambles, smt_file, set_num):
    # print("smt_file", smt_file)
    scramble_file_names = []
    start_i = set_num*num_scrambles
    end_i = start_i + num_scrambles
    for i in range(start_i, end_i):
        # print("scramble i ", i)
        if i == 0:
            with tempfile.NamedTemporaryFile(delete=False) as scramble_file: 
                cp_cmd = f"cp {smt_file} {scramble_file.name}"
                # print("cp_cmd", cp_cmd)
                subprocess.run(cp_cmd, shell=True)
        else:
            seed = scrambler_seed[i]
            with tempfile.NamedTemporaryFile(delete=False) as scramble_file:
                scram_cmd = f"/competition/scrambler  -seed {seed} < {smt_file} > {scramble_file.name}" 
                subprocess.run(scram_cmd, shell=True)
        scramble_file_names.append(scramble_file.name)
    return scramble_file_names


def run_solver(solver_executable, stitched_path, timeout):
    # print("solver executable", solver_executable)
    solve_command = (
        f"{solver_executable} "
        f"{stitched_path} "
    )
    # print("SOLVE COMMAND " + solve_command)
    output = subprocess.run(
        solve_command, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT).stdout.decode("utf-8").strip()
    if "unsat" in output:
        return "unsat"
    elif "sat" in output:
        return "sat"
    elif "timeout" in output:
        return "timeout"
    elif "unknown" in output:
        return "unknown"
    else:
        print(f"the error output is {output}")
        return "error"

