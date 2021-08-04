
# apt

# Description

Install packages by Ansible `apt` module.

Ansible apt module: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html


# How to modify it for your environment

Modify the list of `name` in the task. `state: present` means listed
packages will be installed if not installed. `state: absent` means
packages will be removed if installed. Other options are explained in
the [module
page](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html)