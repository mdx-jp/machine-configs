
# Configuring VMs in mdx with Ansible

This git repository provides an [Ansible](https://www.ansible.com/)
playbook and roles to configure multiple virtual machines in mdx.

We recommend you to briefly read [Ansible overview](https://www.ansible.com/overview/how-ansible-works) and [introduction to playbooks](https://docs.ansible.com/ansible/latest/user_guide/playbooks_intro.html).

## Getting Started

Note that the ansible playbook and roles in this repository assume
that virtual machines are instantiated from the Ubuntu 20.04 template.

1. Install `ansible` on your machine that configures your VMs

2. Download your `user-portal-vm-info.csv` from mdx portal

3. and:

```shell-session
# clone this repository
git clone https://github.com/mdx-jp/machine-configs
cd machine-configs

# create your ansible inventory file 'hosts.ini 'from user-portal-vm-info.csv
./mdxcsv2inventory.py -g nfsserver vm1 -g ldapserver vm1 -g reverseproxy vm1 [PATH-TO]/user-portal-vm-info.csv > hosts.ini
 
# initialize password of mdxuser at VMs to be provisioned
./mdxpasswdinit.py ./hosts.ini
Target hosts: 10.11.4.170, 10.11.0.240, 10.11.4.167, 10.11.4.164, 10.11.4.163, 10.11.4.162
New Password: 
Retype New Password: 
initializing the first password...
10.11.4.170: Success
10.11.0.240: Success
10.11.4.167: Success
10.11.4.164: Success
10.11.4.163: Success
10.11.4.162: Success

# edit playbook.yml to pick roles you want to use
vim playbook.yml

# execute ansible playbook
ansible-playbook -i hosts.ini playbook.yml
```

A detailed instruction is available on [mdx document](https://docs.mdx.jp/ja/).


## Roles

This repository contains following roles:

| Role          | Description | Configurable parameter | 
|:--------------|:------------|:-----------------------|
| common | setup hostname, /etc/hosts, and install packages | [vars/common.yml](vars/common.yml) |
| desktop_common | install xrdp | |
| nfs_server | export /home via NFS | |
| nfs_client | mount /home of an NFS server |  the first host in the host group `nfsserver` is used as the NFS server |
| ldap_server | setup LDAP server | [vars/ldap.yml](vars/ldap.yml) and see [files/README.md](files/README.md) | 
| ldap_client | setup LDAP client | the first host in the host group `ldapserver` is used as the LDAP server |
| jupyter | setup jupyter lab as a daemon process in virtualenv | |
| reverse_proxy | setup reverse proxy for jupyter lab | [vars/reverse_proxy.yml](vars/reverse_proxy.yml) |
| mpi | setup MPI (installed along with OFED) | |


