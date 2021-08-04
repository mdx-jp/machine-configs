
# hosts

## Description

Setup /etc/hosts on all VMs by Ansible `template` module.

Ansible template module: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html


The deployed /etc/hosts file has `IPADDRESS HOSTNAME` lines for all
VMs defined in the inventory file.


## How to modify it for your environment

Modify your inventory file. `IPADDRESS HOSTNAME` mappings are defined
in the inventory file like shown below. `hostname=` is host variable
in Ansible inventory files.

```ini
[default] 

2001:2f8:1041:1b9:250:56ff:feb0:71d hostname=vm1
2001:2f8:1041:1b9:250:56ff:feb0:71f hostname=vm2
2001:2f8:1041:1b9:250:56ff:feb0:721 hostname=vm3
```

Modify IP address and hostname mappings in your inventory file in
accordance with your environment.

Note that it is identical to [`hostname` task](../hostname).

