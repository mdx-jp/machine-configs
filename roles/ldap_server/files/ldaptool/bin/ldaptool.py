#!/usr/bin/python3

"""
ldap_adduser
"""

import getpass
import os
import re
import subprocess

def run(cmd, check=False, **kw):
    """
    run a command
    """
    run_opts = {"shell" : True,
                "encoding" : "utf-8",
                "capture_output" : True}
    run_opts.update(kw)
    comp = subprocess.run(cmd, check=check, **run_opts)
    return comp

def slappasswd(passwd):
    """
    generate passwd hash
    """
    cmd = "slappasswd -s {}".format(passwd)
    try:
        comp = run(cmd, check=True)
    except FileNotFoundError:
        return None
    return comp.stdout.strip()

def ask_password(user):
    """
    ask password
    """
    return getpass.getpass("Password for {}: ".format(user))

def get_next_val_for_attr(ldap_domain, ldap_passwd, attr, firstval):
    """
    find the next available value for attr
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "attr"     : attr,
           "firstval" : firstval}
    cmd = ("ldapsearch -x -w {ldap_passwd}"
           " -D cn=admin,{ldap_domain}"
           " -b ou=people,{ldap_domain}"
           " -LLL {attr}".format(**dic))
    attr_pat = re.compile(r"{attr}: (?P<val>\d+)".format(**dic))
    vals = []
    for line in run(cmd).stdout.strip().split("\n"):
        matched = attr_pat.match(line)
        if matched:
            val = int(matched.group("val"))
            vals.append(val)
    next_val = firstval
    for val in sorted(vals):
        if val < firstval:
            continue
        if val > next_val:
            return next_val
        assert(val == next_val), (val, next_val)
        next_val += 1
    return next_val

def get_next_uid(ldap_domain, ldap_passwd, firstuid):
    """
    find the next available uid
    """
    return get_next_val_for_attr(ldap_domain, ldap_passwd, "uidNumber", firstuid)

def get_next_gid(ldap_domain, ldap_passwd, firstgid):
    """
    find the next available gid
    """
    return get_next_val_for_attr(ldap_domain, ldap_passwd, "gidNumber", firstgid)

def search_for_key(ldap_domain, ldap_passwd, key):
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key}
    search_cmd = ("ldapsearch -x -w {ldap_passwd}"
                  " -D cn=admin,{ldap_domain} -b {key}"
                  .format(**dic))
    comp = run(search_cmd, capture_output=False)
    return comp.returncode

def add_ldif_if_not_exist(ldap_domain, ldap_passwd, key, gen_ldif):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key}
    search_cmd = ("ldapsearch -x -w {ldap_passwd}"
                  " -D cn=admin,{ldap_domain} -b {key}"
                  .format(**dic))
    add_cmd = ("ldapadd -x -w {ldap_passwd}"
               " -D cn=admin,{ldap_domain}"
               .format(**dic))
    if run(search_cmd).returncode == 0:
        print("{key} already exists".format(**dic))
        return 0                # OK
    comp = run(add_cmd, check=True, input=gen_ldif())
    if comp.returncode == 0:
        print("added {key}".format(**dic))
    else:
        print("error during adding {key}".format(**dic))
    return comp.returncode

def add_attr_val_ldif(ldap_domain, ldap_passwd, key, filt, gen_ldif):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key,
           "filter" : filt}
    search_cmd = ("ldapsearch -x -w {ldap_passwd}"
                  " -D cn=admin,{ldap_domain} -b {key} '{filter}'"
                  .format(**dic))
    mod_cmd = ("ldapmodify -x -w {ldap_passwd}"
               " -D cn=admin,{ldap_domain}"
               .format(**dic))
    comp = run(search_cmd)
    if comp.returncode != 0:
        print("{key} does not exist".format(**dic))
        return comp.returncode
    if "numEntries:" in comp.stdout:
        print("{key} exists and already has {filter}".format(**dic))
        return 0
    comp = run(mod_cmd, check=True, input=gen_ldif())
    if comp.returncode == 0:
        print("modified {key}".format(**dic))
    else:
        print("error during modifying {key}".format(**dic))
    return comp.returncode

def del_key_if_exist(ldap_domain, ldap_passwd, key):
    """
    add user to LDAP if it does not exist
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key}
    search_cmd = ("ldapsearch -x -w {ldap_passwd}"
                  " -D cn=admin,{ldap_domain} -b {key}"
                  .format(**dic))
    del_cmd = ("ldapdelete -x -w {ldap_passwd}"
               " -D cn=admin,{ldap_domain} {key}"
               .format(**dic))
    if run(search_cmd).returncode != 0:
        print("{key} does not exist".format(**dic))
        return 0                # OK
    comp = run(del_cmd, check=True)
    if comp.returncode == 0:
        print("deleted {key}".format(**dic))
    else:
        print("error during deleting {key}".format(**dic))
    return comp.returncode

def list_users(info):
    key = "ou=people,{ldap_domain}".format(**info)
    return search_for_key(info["ldap_domain"], info["ldap_passwd"], key)
    
def list_groups(info):
    key = "ou=groups,{ldap_domain}".format(**info)
    return search_for_key(info["ldap_domain"], info["ldap_passwd"], key)
    
def addgroup(info):
    """
    add a group to LDAP if it does not exist
    """
    key = "cn={grp},ou=groups,{ldap_domain}".format(**info)
    def gen_ldif():
        ldif = ("""dn: cn={grp},ou=groups,{ldap_domain}
objectClass: posixGroup
cn: {grp}
gidNumber: {gid}
""".format(**info))
        return ldif
    return add_ldif_if_not_exist(info["ldap_domain"], info["ldap_passwd"], key, gen_ldif)

def adduser(info):
    """
    add user to LDAP if it does not exist
    """
    key = "uid={user},ou=people,{ldap_domain}".format(**info)
    def gen_ldif():
        if info["password_hash"] is None:
            if info["password"] is None:
                if info["ask_password"]:
                    info["password"] = ask_password(info["user"])
            if info["password"] is not None:
                info["password_hash"] = slappasswd(info["password"])
        if info["password_hash"] is None:
            info["user_password_hash"] = ""
        else:
            info["user_password_hash"] = "userPassword: {password_hash}".format(**info)
        ldif = ("""dn: uid={user},ou=people,{ldap_domain}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: {cn}
sn: {sn}
loginShell: {shell}
uidNumber: {uid}
gidNumber: {gid}
homeDirectory: {home}
{user_password_hash}
""".format(**info))
        return ldif
    return add_ldif_if_not_exist(info["ldap_domain"], info["ldap_passwd"], key, gen_ldif)

def make_home(info):
    """
    make a home directory for user (dictionary)
    """
    home = info["home"]
    perm = info["home_perm"]
    uid_num = int(info["uid"])
    gid_num = int(info["gid"])
    pub_keys = info["authorized_keys"]
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
    return 0                    # OK

def add_user_to_group(info, extra_group):
    """
    add user to group
    """
    key = ("cn={extra_group},ou=groups,{ldap_domain}"
           .format(extra_group=extra_group, **info))
    filt = "(memberUid={user})".format(**info)
    def gen_ldif():
        ldif = ("""dn: cn={extra_group},ou=groups,{ldap_domain}
changetype: modify
add: memberUid
memberUid: {user}""".format(extra_group=extra_group, **info))
        return ldif
    return add_attr_val_ldif(info["ldap_domain"], info["ldap_passwd"],
                             key, filt, gen_ldif)

def adduser_group_home(info):
    """
    add user, its primary group, and home dir
    """
    err = adduser(info)
    if err:
        return err
    err = addgroup(info)
    if err:
        return err
    err = 0 if info["no_create_home"] else make_home(info)
    if err:
        return err
    for extra_group in info["groups"]:
        err = add_user_to_group(info, extra_group)
        if err:
            return err
    return err

def delgroup(info):
    """
    delete group given in info
    """
    key = "cn={grp},ou=groups,{ldap_domain}".format(**info)
    return del_key_if_exist(info["ldap_domain"], info["ldap_passwd"], key)

def deluser(info):
    """
    delete user given in info
    """
    key = "uid={user},ou=people,{ldap_domain}".format(**info)
    return del_key_if_exist(info["ldap_domain"], info["ldap_passwd"], key)

def get_default_ldap_domain():
    """
    get ldap domain
    """
    pat = re.compile("^base +(?P<dom>.*)$")
    with open("/etc/ldap.conf") as conf_fp:
        for line in conf_fp:
            matched = pat.match(line)
            if matched:
                return matched.group("dom")
    return ""

def get_default_ldap_passwd():
    """
    get ldap passwd
    """
    with open("/etc/ldap.secret") as pwd_fp:
        return pwd_fp.read()
