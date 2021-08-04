
# machine provisioner with ansible at mdx

This is a git repository provides examples and templates to provision
configurations in multiple VM instances in mdx. This provisioner
leverages [Ansible](https://www.ansible.com/), a open-source software
for provisioning and configuring machines.


We recommend you to briefly read [an overview](https://www.ansible.com/overview/how-ansible-works) and [an introduction to playbooks](https://docs.ansible.com/ansible/latest/user_guide/playbooks_intro.html)


## Getting Started

1. Install `ansible` on your machine that configures your VMs.

2. Prepare your Ansible inventory file, which contains IP addresses of
VMs (called managed nodes in the Ansible context) to be provisioned.
[sample-inventory.ini](sample-inventory.ini) is a sample file. The
minimum modification to the sample you need is to change the IP
addresses to your VMs' addresses.

3. Prepare your Ansible playbook file, which defines tasks to be done
on the VMs. [sample-playbook.yml](sample-playbook.yml) is a sample
file.

4. Run `ansible-playbook` command with your inventory and playbook like:

```shell-session
ansible-playbook -i my-hosts.ini my-playbook.yml
```

Then ansible starts to ssh to the VMs and configure them as you
defined in your playbook.


[tasks](tasks) directory contains ansible tasks, which are popular tasks in
mdx. Some tasks are general (e.g., install specified packages on all
VMs), and some tasks are used to build Virtual Machine Template in mdx
(e.g., configure network interfaces via netplan).

You can use these tasks in this repository as is, however,
configurations usually depend on use cases, purposes, environments of
each user. Thus, you can modify the files in this repository to
provision your environments for your purpose. This repository provides
the first step and templates for that.



## Tasks

General tasks:
- [apt](tasks/apt): install packages
- [hostname](tasks/hostname): configure hostname of each VM
- [hosts](tasks/hosts): deploy appropriate /etc/hosts on VMs
- [users](tasks/users): add/del UNIX user accounts on VMs


Example tasks (environment-dependent)
- [apache](tasks/apache): install apache2 web server and put a index.html
- [docker](tasks/docker): install Docker Engine
- [jupyterlab](tasks/jupyterlab): daemonize and run jupyter lab
- [nfs](tasks/nfs): an example to deploy a NFS server and NFS clients


Template build tasks:
- cloud-init
- netplan
- sshd
- ntp
- vm-*