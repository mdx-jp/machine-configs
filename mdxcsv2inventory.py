#!/usr/bin/env python3

import argparse
import csv
import sys
import json
import re
from ipaddress import ip_network, ip_address

def csv2dictlist(csvfile):
    reader = csv.DictReader(csvfile)
    return [ row for row in reader ]

def validate_vms(vms, enable_linklocal):
    """
    Validate values for *_IPv* are IP addresses
    """
    for vm in vms:
        for key in vm.keys():
            if vm[key] and "_IPv" in key:
                try:
                    addr = ip_address(vm[key])
                    if (not enable_linklocal and
                        addr.version == 6 and addr.is_link_local):
                        vm[key] = ""
                except ValueError:
                    vm[key] = ""


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

        if vm["SERVICE_NET_1_IPv6"] and args.enable_ethipv6:
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
            if ethipv6prefix.is_link_local:
                continue

            return ethipv6prefix

    return None


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

def generate_group_regexp(vms, args, group_args, invert = False):

    w = lambda x: args.output.write(x + "\n")

    for attrs in group_args:
        groupname = attrs[0]
        regexp = re.compile(attrs[1])

        if not invert:
            f = lambda v: regexp.search(v["VM_NAME"])
            m = "with"
        else:
            f = lambda v: not regexp.search(v["VM_NAME"])
            m = "without"

        w("[{}]".format(groupname))
        w("# group {} regexp '{}'".format(m, attrs[1]))
        for vm in filter(f, vms):
            printvm(vm, args)
        w("")

def generate_inventory(args):

    vms = csv2dictlist(args.csv)
    validate_vms(vms, args.enable_linklocal)
    vms.sort(key = lambda x: x["VM_NAME"])
    ethipv4prefix, rdmaipv4prefix = get_ipv4prefix(vms)
    ethipv6prefix = get_ipv6prefix(vms)

    w = lambda x: args.output.write(x + "\n")

    # write vars for all node group
    w("[all:vars]")
    w("ansible_user={}".format(args.ansible_user))
    w("ansible_remote_tmp=/tmp/.ansible")
    w("ldap_vars_file=vars/ldap.yml")
    if ethipv4prefix:
        w("ethipv4prefix={}".format(ethipv4prefix))
    else:
        w("# no valid IPv4 prefix for Ethernet network found")
    if rdmaipv4prefix:
        w("rdmaipv4prefix={}".format(rdmaipv4prefix))
    else:
        w("# no valid IPv4 prefix for RDMA network found")
    if ethipv6prefix:
        w("ethipv6prefix={}".format(ethipv6prefix))
    else:
        w("# no valid IPv6 prefix for Ethernet network found")
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

    # write groups with regexp
    if args.group_regexp:
        generate_group_regexp(vms, args, args.group_regexp, invert = False)

    # write groups with regexp
    if args.group_regexp_invert:
        generate_group_regexp(vms, args, args.group_regexp_invert,
                              invert = True)

    # write per-node groups
    if args.per_node_groups:
        for vm in filter(lambda v: v["SERVICE_NET_1_IPv4"], vms):
            w("[{}]".format(vm["VM_NAME"]))
            printvm(vm, args)
            w("")
            

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("csv",
                        type = argparse.FileType("r", encoding = "utf_8_sig"),
                        help = "CSV file generated by mdx user portal")

    parser.add_argument("-6", "--use-ipv6", action = "store_true",
                        help = "use IPv6 address for hosts")
    parser.add_argument("-u", "--ansible-user", default = "mdxuser",
                        help = "user to run ansible, default is mdxuser")
    parser.add_argument("-d", "--default-group", default = "default",
                        help = "group name for all nodes, default is default")
    parser.add_argument("-g", "--group-regexp", nargs = 2, action = "append",
                        metavar = ("GROUP", "REGEXP"),
                        help = ("make a group GROUP with " +
                                "VM names matched with REGEXP"))
    parser.add_argument("-gv", "--group-regexp-invert",
                        nargs = 2, action = "append",
                        metavar = ("GROUP", "REGEXP"),
                        help = ("make a group GROUP without " +
                                "VM names matched with REGEXP"))
    parser.add_argument("--group-with", nargs = "+", action = "append",
                        metavar = ("GROUP", "VM_NAME"),
                        help = "make a group with specified VM names")
    parser.add_argument("--group-without", nargs = "+", action = "append",
                        metavar = ("GROUP", "VM_NAME"),
                        help = "make a group without specified VM names ")
    parser.add_argument("--per-node-groups", action = "store_true",
                        help = "make per-node groups in the inventory")
    parser.add_argument("--enable-ethipv6", action = "store_true",
                        help = "enable host var 'ethipv6'")
    parser.add_argument("--enable-linklocal", action = "store_true",
                        help = "enable IPv6 link locak address on inventory")
    parser.add_argument("--output", type = argparse.FileType("w"),
                        default = sys.stdout,
                        help = "output file name, default is STDOUT")

    args = parser.parse_args()

    generate_inventory(args)


if __name__ == "__main__":
    main()
