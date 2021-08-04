
# hostname

## Description

Setup hostname of each VM by Ansible `hostname` module.

Ansible hostname module: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/hostname_module.html

Hostname for a VM (specified by an IP address) is defined as host
variable in the inventory file. Please see the sample inventory file
[sample-hosts.ini](../sample-hosts.ini).



## How to modify it for your environment

Modify your inventory file. Define host variable
`hostname=Your_Host_Name` behind an IP address like shown below:

```ini
[default] 

2001:2f8:1041:1b9:250:56ff:feb0:71d hostname=vm1
2001:2f8:1041:1b9:250:56ff:feb0:71f hostname=vm2
2001:2f8:1041:1b9:250:56ff:feb0:721 hostname=vm3
```

In this example, a managed node having IPv6 address
2001:2f8:1041:1b9:250:56ff:feb0:71d is configured as hostname
`vm1`.

Modify IP address and hostname mappings in your inventory file in
accordance with your environment.
