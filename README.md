
# machine provisioner with ansible at mdx

This is a git repositry to provision configurations in multiple VM
instances in mdx. This provisioning leverages
[Ansible](https://www.ansible.com/), a open-source software for
provisioning and configuring machines.


## Getting Started

1. Install `ansible` on your machine that configures your VMs.

2. Prepare your Ansible inventory file, which contains IP addresses of
VMs (called managed nodes in the Ansbile context) to be provisioned.
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