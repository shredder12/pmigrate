#!/usr/bin/env python

import argparse
import subprocess
import os
import sys
from subprocess import CalledProcessError
from psutil import Process
from fabric.api import env
from fabric.operations import run, sudo, put

data_dir="/tmp/data"
criu_exec="/home/ubuntu/criu-1.2/criu"

def parse_arguments():
    ''' Parsing arguments of the proc_migrate cli tool '''

    parser = argparse.ArgumentParser(description='Live migration of processes')
    parser.add_argument("-p", "--pid", type=int, help="process id", required=True)
    parser.add_argument("-H", "--host", help="destination hostname or IP", required=True)
    parser.add_argument("-u", "--user", help="user to use when logging into destination host", required=True)
    parser.add_argument("-s", "--sudo", help="use sudo to execute privilege commands", action="store_true")
    
    args = parser.parse_args()

    return args    

def common_option(pid):
    ''' common options to be used in both restore and dump '''

    options = list()
    proc = Process(pid)
    if proc.terminal():
        options.append("--shell-job")
    if proc.connections(kind="inet"):
        options.append("--tcp-established")

    return options

def dump(pid, options):
    ''' Dump process tree memory state '''

    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)

    cmd = ("{0} dump -t {1} -D {2}".format(criu_exec, str(pid), data_dir)).split()
    cmd += options

    try:
        print ' '.join(cmd)
        dump_ret = subprocess.check_call(cmd)

    except CalledProcessError as e:
        print(e.returncode)
        print ' '.join(e.cmd)
        sys.exit(1)

def transfer_files(proc_files):
    ''' Transfer the dump and open files to the destination node '''

    for proc_file in proc_files:
        print proc_file.path
        put(proc_file.path, mirror_local_mode=True)

    put(data_dir, os.path.dirname(data_dir))

def restore(options):
    ''' Restores process state on the destination machine '''


    # Err: Restore detach doesn't work
    cmd = ("{0} restore -D {1}".format(criu_exec, data_dir).split())
    cmd += options

    if env.user != 'root':
        print ' '.join(cmd)
        sudo(' '.join(cmd))
    else:
        print ' '.join(cmd)
        run(' '.join(cmd))

if __name__ == '__main__':
    args = parse_arguments()
    env.user = args.user
    env.host_string = args.host
    proc = Process(args.pid)
    proc_files = proc.open_files()
    
    options = common_option(args.pid)
    print options
    dump(args.pid, options)
    # Transfer the dump and files to the destination node
    transfer_files(proc_files)
    restore(options)
