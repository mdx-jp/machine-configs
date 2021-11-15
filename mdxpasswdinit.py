#!/usr/bin/env python3

import argparse
import getpass
import pexpect
import multiprocessing as mp
import sys


from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager

def pr_exit(string):
    print(string, file = sys.stderr)
    sys.exit(1)


def load_hosts_from_inventory(args):

    loader = DataLoader()
    inventory = InventoryManager(loader = loader, sources = args.inventory)
    
    if not args.group in inventory.groups:
        pr_exit("no group '{}' found in '{}'".format(args.group,
                                                     args.inventory))

    return list(map(str, inventory.groups[args.group].serialize()["hosts"]))


def set_first_password(mparg):

    (args, host) = mparg

    ssh_args = ("-o StrictHostKeyChecking=no " +
                "-o UserKnownHostsFile=/dev/null " +
                "-o PreferredAuthentications=publickey")
    cmd = "ssh {} {} -l {} {}".format(ssh_args, args.ssh_args, args.user, host)

    conn = pexpect.spawn(cmd, timeout = args.timeout)

    ret = "Success"

    try:
        conn.expect("New password: ")
        conn.sendline(args.password)
        conn.expect("Retype new password: ")
        conn.sendline(args.password)
        conn.expect("passwd: password updated successfully")
    except Exception as e:
        for line in str(e).split("\n"):
            if "buffer (last 100 chars)" in line:
                ret = line
        
    return (host, ret)


def main():

    desc = "set mdxuser password at first time"

    parser = argparse.ArgumentParser(description = desc)
    parser.add_argument("inventory",
                        metavar = "INVENTORY",
                        help = "ansible inventory file")
    parser.add_argument("-u", "--user", default = "mdxuser",
                        help = "ssh login user, default is 'mdxuser'")
    parser.add_argument("-g", "--group", default = "default",
                        help = ("group of VMs in the inventory to " +
                                "initialize passowrd, default is 'default'"))
    parser.add_argument("-t", "--timeout", default = 5,
                        help = "timeout to ssh and wait 'New password:'")
    parser.add_argument("--f", "--forks", default = 30,
                        help = "number of fork processes, default is 30")
    parser.add_argument("--ssh-args", default = "",
                        help = "arguments for ssh to VMs")
    
    args = parser.parse_args()

    hosts = load_hosts_from_inventory(args)
    if not hosts:
        pr_exit("No host found in gorup '{}' in '{}'".format(args.group,
                                                             args.inventory))
    print("Target hosts: {}".format(", ".join(hosts)))

    password = getpass.getpass(prompt = "New Password: ")
    verify = getpass.getpass(prompt = "Retype New Password: ")
    if password != verify:
        pr_exit("Password mismatch")

    setattr(args, "password", password)


    print("initializing the first password...")
    mpargs = []
    for host in hosts:
        mpargs.append((args, host))

    with mp.Pool(processes = 30) as p:
        rets = p.map(set_first_password, mpargs)

    for ret in rets:
        print("{}: {}".format(ret[0], ret[1]))



if __name__ == "__main__":
    main()
