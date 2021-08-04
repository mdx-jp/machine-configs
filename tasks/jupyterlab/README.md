
# jupyterlab

## Description

Install jupyter, daemonize jupyter lab through systemd, and run
jupyter lab.

daemonize a process is done by putting a systemd unit file
/etc/systemd/system/jupyterlab.service. This file is generated
by Ansible template module by a task shown below:

```yml
- name: daemonize jupyterlab through systemd
  template:
    src: templates/jupyterlab.service.j2
    dest: /etc/systemd/system/jupyterlab.service
```

The unit file is generated from
[templates/jupyterlab.service.j2](templates/jupyterlab.service.j2).

```
[Unit]
Description=jupyter lab daemon

[Service]
Type=simple
WorkingDirectory={{ jupyterlab_directory }}
ExecStart=/usr/local/bin/jupyter lab --ip=:: --NotebookApp.token=""
Restart=always
User={{ jupyterlab_user }}
Group={{ jupyterlab_group }}

[Install]
WantedBy=multi-user.target
```

As shown, user, group, and working directory can be changed through
variables defined in [vars/jupyterlab.yml](vars/jupyterlab.yml).

## How to modify it for your environment

Modify variables in [vars/jupyterlab.yml](vars/jupyterlab.yml) to
change user/group and working directory of jupyterlab.

Note that the systemd unit file executes jupyter lab on IPv6 `--ip=::`
without token `--NotebookApp.token=""`. Make sure that you have IPv6
and IPv6 ACL on your mdx project is properly configured.