
# NFS

## Description

An example to configure a VM as a NFS server, and other two VMs as NFS
clients by Ansible.


[common.yml](common.yml) creates /export directory and install
nfs-common on all VMs.

[server.yml](server.yml) installs NFS server packages, and exports the
/export directory at the NFS server VM.

[client.yml](client.yml) mounts /export on the NFS server onto /export
via NFS.


The inventory file, [sample-hosts.ini](sample-hosts.ini), VM/Role
mapping is defined by host grouping.



