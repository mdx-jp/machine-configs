#!/usr/bin/env python3

import argparse
import csv
import sys
import json
from ipaddress import ip_network

def csv2dictlist(csvfile):
    reader = csv.DictReader(csvfile)
    return [ row for row in reader ]

def printvm(vm, args):

    keys = ["SERVICE_NET_1_IPv4", "SERVICE_NET_1_IPv6"]
    if args.use_ipv6:
        keys.reverse()

    addr = None
    for key in keys:
        if vm[key]:
            addr = vm[key]
            break

    if not addr:
        out = "# !! no service address available for {}".format(vm["VM_NAME"])
    else:
        out = "{:<15} hostname={}".format(addr, vm["VM_NAME"])

        if vm["SERVICE_NET_1_IPv4"]:
            out += " ethipv4={:<15}".format(vm["SERVICE_NET_1_IPv4"])

        if vm["STORAGE_NET_1_IPv4"]:
            out += " rdmaipv4={:<15}".format(vm["STORAGE_NET_1_IPv4"])

        if vm["SERVICE_NET_1_IPv6"] and not args.disable_ethipv6:
            out += " ethipv6={:<15}".format(vm["SERVICE_NET_1_IPv6"])

    args.output.write(out + "\n")

def get_ipv4prefix(vms):
    # XXX: Assuming SERVICE|STORAGE_NET_1
    ethipv4prefix = None
    rdmaipv4prefix = None
    for vm in vms:
        if vm["SERVICE_NET_1_IPv4"]:
            ethipv4prefix = ip_network(vm["SERVICE_NET_1_IPv4"] + "/21",
                                         strict = False)
        if vm["STORAGE_NET_1_IPv4"]:
            rdmaipv4prefix = ip_network(vm["STORAGE_NET_1_IPv4"] + "/21",
                                        strict = False)
        if ethipv4prefix and rdmaipv4prefix:
            break
    return ethipv4prefix, rdmaipv4prefix

def get_ipv6prefix(vms):
    # XXX: Assuming SERVICE_NET_1
    ethipv6prefix = None
    for vm in vms:
        if vm["SERVICE_NET_1_IPv6"]:
            ethipv6prefix = ip_network(vm["SERVICE_NET_1_IPv6"] + "/64",
                                       strict = False)
    return ethipv6prefix


def generate_group_with(vms, args):

    w = lambda x: args.output.write(x + "\n")

    for attrs in args.group_with:
        groupname = attrs.pop(0)
        if not attrs:
            msg = "no VM name specifeid for --group-with {}".format(groupname)
            raise AttributeError(msg)

        w("[{}]".format(groupname))
        w("# group with {}".format(" ".join(attrs)))
        for vm in filter(lambda v: v["VM_NAME"] in attrs, vms):
            printvm(vm, args)
        w("")

def generate_group_without(vms, args):

    w = lambda x: args.output.write(x + "\n")

    for attrs in args.group_without:
        groupname = attrs.pop(0)

        w("[{}]".format(groupname))
        w("# group without {}".format(" ".join(attrs)))
        for vm in filter(lambda v: not v["VM_NAME"] in attrs, vms):
            printvm(vm, args)
        w("")


def generate_inventory(args):

    vms = csv2dictlist(args.csv)
    vms.sort(key = lambda x: x["VM_NAME"])
    ethipv4prefix, rdmaipv4prefix = get_ipv4prefix(vms)
    ethipv6prefix = get_ipv6prefix(vms)

    w = lambda x: args.output.write(x + "\n")

    # write vars for all node group
    w("[all:vars]")
    w("ansible_user={}".format(args.ansible_user))
    if ethipv4prefix:
        w("ethipv4prefix={}".format(ethipv4prefix))
    if rdmaipv4prefix:
        w("rdmaipv4prefix={}".format(rdmaipv4prefix))
    if ethipv6prefix:
        w("ethipv6prefix={}".format(ethipv6prefix))
    w("")

    # write a group that contains all nodes
    w("[{}]".format(args.default_group))
    for vm in vms:
        printvm(vm, args)
    w("")
    
    # write user-specified groups
    if args.group_with:
        generate_group_with(vms, args)

    if args.group_without:
        generate_group_without(vms, args)

    # write per-node groups
    if args.per_node_groups:
        for vm in filter(lambda v: v["SERVICE_NET_1_IPv4"], vms):
            w("[{}]".format(vm["VM_NAME"]))
            printvm(vm, args)
            w("")
            

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-6", "--use-ipv6", action = "store_true",
                        help = "use IPv6 address for hosts")
    parser.add_argument("-u", "--ansible-user", default = "mdxuser",
                        help = "user to run ansible, default is mdxuser")
    parser.add_argument("-g", "--default-group", default = "default",
                        help = "group name for all nodes, default is default")
    parser.add_argument("--per-node-groups", action = "store_true",
                        help = "make per-node groups in the inventory")
    parser.add_argument("--group-with", nargs = "+", action = "append",
                        metavar = ("GROUP", "VM_NAME"),
                        help = "make a group with specified VM names")
    parser.add_argument("--group-without", nargs = "+", action = "append",
                        metavar = ("GROUP", "VM_NAME"),
                        help = "make a group without specified VM names ")
    parser.add_argument("--disable-ethipv6", action = "store_true",
                        help = "disable host var 'ethipv6'")
    parser.add_argument("--output", type = argparse.FileType("w"),
                        default = sys.stdout,
                        help = "output file name, default is STDOUT")
    parser.add_argument("csv",
                        type = argparse.FileType("r", encoding = "utf_8_sig"),
                        help = "CSV file generated by mdx user portal")

    args = parser.parse_args()

    generate_inventory(args)


if __name__ == "__main__":
    main()
