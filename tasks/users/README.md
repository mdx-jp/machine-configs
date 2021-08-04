
# users

## Description

Provision users' unix accounts by Ansible `user` module, and put ssh
authorized keys by `authorized_key` module.

- Ansible user module: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/user_module.html
- Ansible authorized_key module: https://docs.ansible.com/ansible/latest/collections/ansible/posix/authorized_key_module.html


## How to modify it for your environment

(1) Modify [vars/userlist.yml](vars/userlist.yml) that defines user
accounts, and (2) put ssh authorized key files in `public_keys`
directory.

Information of user accounts are defined as a varible in
vars/userlist.yml and a protion is shown below.

```yml
users:
  - name: prjuser1
    state: present
    password: $6$ultraslt$b47IR6oT4WndhJ4AiP9hP1s7R8COiJR9G1GY5xM39jSwB4FGiYNSv6Cfb364ECeAhqUiDQLConHh.f1ocFVfZ1
    key: "{{lookup('file', 'public_keys/prjuser1.key')}}"
    groups: adm,sudo
```

`name` is user name. `state: present` indicates this user account
should exist; if it does not exist, it will be created. If
`state:absent` and the user account exist, the account is deleted.

`key: "{{lookup('file', 'public_keys/prjuser1.key')}}"` extracts ssh
keys in file [public_keys/prjuser1.key](public_keys/prjuser1.key), and
the content is deployed in `/home/prjuser1/.ssh/authorized_keys`.

These variables are passed to the ansible modules in
[task.yml](task.yml). task.yml uses `include_vars` module to load the
variable defined in vars/userlist.yml.

- ANsible include_vars module: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/include_vars_module.html


You can add/delete unix accounts in your VMs by describing account
information in vars/userlist.yml and put ssh keys in public_keys
directory.