#!/usr/bin/python3
"""
make_users_groups

make users and groups from csv files
- users_csv
- groups_csv
"""

import argparse
import csv
import os
import subprocess
import sys

def make_home(user):
    """
    make a home directory for user (dictionary)
    """
    home = user["homedirectory"]
    perm = user["homedirectory_perm"]
    uid_num = int(user["uidnumber"])
    gid_num = int(user["gidnumber"])
    pub_keys = user["authorized_keys"]
    parent_dir = os.path.dirname(home)
    dot_ssh = "{}/.ssh".format(home)
    authorized_keys = "{}/authorized_keys".format(dot_ssh)
    os.makedirs(parent_dir, exist_ok=True, mode=0o755)
    os.chown(parent_dir, uid=0, gid=0)
    os.makedirs(home, exist_ok=True,
                mode=int(perm, 8))
    os.chown(home, uid=uid_num, gid=gid_num)
    if pub_keys:
        os.makedirs(dot_ssh, exist_ok=True, mode=0o700)
        os.chown(dot_ssh, uid=uid_num, gid=gid_num)
        if not os.path.exists(authorized_keys):
            with open(authorized_keys, "w") as auth_key_wp:
                auth_key_wp.write(pub_keys)
            os.chown(authorized_keys, uid=uid_num, gid=gid_num)
            os.chmod(authorized_keys, 0o600)
    return 1                    # OK

def run(cmd, input_str):
    """
    run a command
    """
    print(cmd)
    comp = subprocess.run(cmd, shell=True, input=input_str, encoding="utf-8", check=False)
    print("--> {}".format(comp.returncode))
    return comp.returncode

def slappasswd(passwd):
    try:
        comp = subprocess.run(["slappasswd", "-s", passwd],
                              capture_output=True,
                              check=False, encoding="utf-8")
    except FileNotFoundError:
        return ""
    return comp.stdout.strip()

def add_ldif_if_not_exist(ldap_domain, ldap_passwd, key, ldif):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key}
    cmd = ("if ! ldapsearch -x -w {ldap_passwd}"
           " -D cn=admin,{ldap_domain}"
           " -b {key}"
           " > /dev/null; then"
           " ldapadd -x -w {ldap_passwd}"
           " -D cn=admin,{ldap_domain} ;"
           "fi" .format(**dic))
    return run(cmd, ldif)

def add_user_if_not_exist(ldap_passwd, ldap_domain, user):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain}
    dic.update(user)
    if not dic["password_hash"] and dic["password"]:
        dic["password_hash"] = slappasswd(dic["password"])
    key = "uid={uid},ou=people,{ldap_domain}".format(**dic)
    ldif = ("""dn: uid={uid},ou=people,{ldap_domain}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: {cn}
sn: {sn}
userPassword: {password_hash}
loginShell: {loginshell}
uidNumber: {uidnumber}
gidNumber: {gidnumber}
homeDirectory: {homedirectory}
""".format(**dic))
    return add_ldif_if_not_exist(ldap_domain, ldap_passwd, key, ldif)

def add_group_if_not_exist(ldap_passwd, ldap_domain, group):
    """
    add a group to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain}
    dic.update(group)
    key = "cn={gid},ou=groups,{ldap_domain}".format(**dic)
    ldif = ("""dn: cn={gid},ou=groups,{ldap_domain}
objectClass: posixGroup
cn: {gid}
gidNumber: {gidnumber}
""".format(**dic))
    return add_ldif_if_not_exist(ldap_domain, ldap_passwd, key, ldif)

def add_user_if_not_exist_x(ldap_passwd, ldap_domain, user):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain, "ldap_passwd" : ldap_passwd}
    dic.update(user)
    cmd = ("if ! ldapsearch -x -w {ldap_passwd}"
           " -D cn=admin,{ldap_domain}"
           " -b uid={uid},ou=people,{ldap_domain}"
           " > /dev/null; then"
           " ldapadd -x -w {ldap_passwd}"
           " -D cn=admin,{ldap_domain} ;"
           "fi" .format(**dic))
    ldif = ("""dn: uid={uid},ou=people,{ldap_domain}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: {cn}
sn: {sn}
userPassword: {password_hash}
loginShell: {loginshell}
uidNumber: {uidnumber}
gidNumber: {gidnumber}
homeDirectory: {homedirectory}
""".format(**dic))
    return run(cmd, ldif)

def add_group_if_not_exist_x(ldap_passwd, ldap_domain, group_dict):
    """
    add a group to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain, "ldap_passwd" : ldap_passwd}
    dic.update(group_dict)
    cmd = ("if ! ldapsearch -x -w {password}"
           " -D cn=admin,{ldap_domain}"
           " -b cn={gid},ou=groups,{ldap_domain}"
           " > /dev/null; then"
           " ldapadd -x -w {password}"
           " -D cn=admin,{ldap_domain} ;"
           "fi".format(**dic))
    ldif = ("""dn: cn={gid},ou=groups,{ldap_domain}
objectClass: posixGroup
cn: {gid}
gidNumber: {gidnumber}
""".format(**dic))
    return run(cmd, ldif)

def add_users_groups(opts):
    """
    add all users and groups in ldap_users_csv and ldap_groups_csv
    """
    ldap_passwd = opts.password
    ldap_domain = opts.domain
    ldap_users_csv = opts.users
    ldap_groups_csv = opts.groups
    if ldap_users_csv:
        with open(ldap_users_csv) as users_fp:
            ldap_users_list = list(csv.DictReader(users_fp))
            for user in ldap_users_list:
                retc = add_group_if_not_exist(ldap_passwd, ldap_domain, user)
                if retc:
                    return retc
                retc = add_user_if_not_exist(ldap_passwd, ldap_domain, user)
                if retc:
                    return retc
                if make_home(user) == 0:
                    return 1    # NG
    if ldap_groups_csv:
        with open(ldap_groups_csv) as groups_fp:
            ldap_groups_list = list(csv.DictReader(groups_fp))
            for group in ldap_groups_list:
                retc = add_group_if_not_exist(ldap_passwd, ldap_domain, group)
                if retc:
                    return 1
    return 0                    # OK

def parse_args(argv):
    """
    parse comand line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("password", help="LDAP domain password")
    parser.add_argument("domain", help="LDAP domain (e.g., dc=myldap,dc=mdx,dc=jp")
    parser.add_argument("--users", help="CSV file listing users")
    parser.add_argument("--groups", help="CSV file listing groups")
    args = parser.parse_args(argv[1:])
    return args

def main():
    """
    main
    """
    opts = parse_args(sys.argv)
    if add_users_groups(opts) == 0:
        return 0                # OK
    return 1                    # NG

if __name__ == "__main__":
    sys.exit(main())
