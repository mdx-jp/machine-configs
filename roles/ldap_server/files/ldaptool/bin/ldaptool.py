#!/usr/bin/python3

"""
ldap_adduser
"""

import getpass
import os
import re
import subprocess

def run(cmd, info, check=False, **kw):
    """
    run a command
    """
    run_opts = {"shell" : True,
                "encoding" : "utf-8",
                "capture_output" : True}
    run_opts.update(kw)
    if info["verbose"]:
        print(f"cmd: {cmd}", flush=True)
    if info["run"]:
        comp = subprocess.run(cmd, check=check, **run_opts)
    else:
        comp = subprocess.run("true")
    return comp

def slappasswd(passwd, info):
    """
    generate passwd hash
    """
    cmd = f"slappasswd -s {passwd}"
    try:
        comp = run(cmd, info, check=True)
    except FileNotFoundError:
        return None
    return comp.stdout.strip()

def ask_password(user):
    """
    ask password
    """
    return getpass.getpass(f"Password for {user}: ")

def get_next_val_for_attr(ldap_domain, ldap_passwd, attr, firstval, info):
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
    attr_pat = re.compile(fr"{attr}: (?P<val>\d+)")
    vals = []
    for line in run(cmd, info).stdout.strip().split("\n"):
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

def get_next_uid(ldap_domain, ldap_passwd, firstuid, info):
    """
    find the next available uid
    """
    return get_next_val_for_attr(ldap_domain, ldap_passwd, "uidNumber", firstuid, info)

def get_next_gid(ldap_domain, ldap_passwd, firstgid, info):
    """
    find the next available gid
    """
    return get_next_val_for_attr(ldap_domain, ldap_passwd, "gidNumber", firstgid, info)

def search_for_key(ldap_domain, ldap_passwd, key, info):
    """
    search the domain for key
    """
    dic = {"ldap_domain" : ldap_domain,
           "ldap_passwd" : ldap_passwd,
           "key" : key}
    search_cmd = ("ldapsearch -x -w {ldap_passwd}"
                  " -D cn=admin,{ldap_domain} -b {key}"
                  .format(**dic))
    comp = run(search_cmd, info, capture_output=False)
    return comp.returncode

def add_ldif_if_not_exist(ldap_domain, ldap_passwd, key, gen_ldif, info):
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
    if run(search_cmd, info).returncode == 0:
        print(f"{key} already exists")
        return 0                # OK
    comp = run(add_cmd, info, check=True, input=gen_ldif())
    if comp.returncode == 0:
        print(f"added {key}")
    else:
        print(f"error during adding {key}")
    return comp.returncode

def add_attr_val_ldif(ldap_domain, ldap_passwd, key, filt, gen_ldif, info):
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
    comp = run(search_cmd, info)
    if comp.returncode != 0:
        print(f"{key} does not exist")
        return comp.returncode
    if "numEntries:" in comp.stdout:
        print("{key} exists and already has {filter}".format(**dic))
        return 0
    comp = run(mod_cmd, info, check=True, input=gen_ldif())
    if comp.returncode == 0:
        print(f"modified {key}")
    else:
        print(f"error during modifying {key}")
    return comp.returncode

def del_key_if_exist(ldap_domain, ldap_passwd, key, info):
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
    if run(search_cmd, info).returncode != 0:
        print(f"{key} does not exist")
        return 0                # OK
    comp = run(del_cmd, info, check=True)
    if comp.returncode == 0:
        print(f"deleted {key}")
    else:
        print(f"error during deleting {key}")
    return comp.returncode

def list_users(info):
    """
    list of all users
    """
    key = f'ou=people,{info["ldap_domain"]}' # .format(**info)
    return search_for_key(info["ldap_domain"], info["ldap_passwd"], key, info)

def list_groups(info):
    """
    list of all groups
    """
    key = f'ou=groups,{info["ldap_domain"]}' # .format(**info)
    return search_for_key(info["ldap_domain"], info["ldap_passwd"], key, info)

def addgroup(info):
    """
    add a group to LDAP if it does not exist
    """
    key = f'cn={info["grp"]},ou=groups,{info["ldap_domain"]}' # .format(**info)
    def gen_ldif():
        ldif = f'''dn: cn={info["grp"]},ou=groups,{info["ldap_domain"]}
objectClass: posixGroup
cn: {info["grp"]}
gidNumber: {info["gid"]}
''' # .format(**info)
        return ldif
    return add_ldif_if_not_exist(info["ldap_domain"], info["ldap_passwd"], key, gen_ldif, info)

def adduser(info):
    """
    add user to LDAP if it does not exist
    """
    key = f'uid={info["user"]},ou=people,{info["ldap_domain"]}' # .format(**info)
    def gen_ldif():
        if info["password_hash"] is None:
            if info["password"] is None:
                if info["ask_password"]:
                    info["password"] = ask_password(info["user"])
            if info["password"] is not None:
                info["password_hash"] = slappasswd(info["password"], info)
        if info["password_hash"] is None:
            info["user_password_hash"] = ""
        else:
            info["user_password_hash"] = f'userPassword: {info["password_hash"]}' # .format(**info)
        ldif = f'''dn: uid={info["user"]},ou=people,{info["ldap_domain"]}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: {info["cn"]}
sn: {info["sn"]}
loginShell: {info["shell"]}
uidNumber: {info["uid"]}
gidNumber: {info["gid"]}
homeDirectory: {info["home"]}
{info["user_password_hash"]}
'''# .format(**info))
        return ldif
    return add_ldif_if_not_exist(info["ldap_domain"], info["ldap_passwd"], key, gen_ldif, info)

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
    dot_ssh = f"{home}/.ssh"
    authorized_keys = f"{dot_ssh}/authorized_keys"# .format(dot_ssh)
    os.makedirs(parent_dir, exist_ok=True, mode=0o755)
    os.chown(parent_dir, uid=0, gid=0)
    os.makedirs(home, exist_ok=True,
                mode=int(perm, 8))
    os.chown(home, uid=uid_num, gid=gid_num)
    if pub_keys:
        os.makedirs(dot_ssh, exist_ok=True, mode=0o700)
        os.chown(dot_ssh, uid=uid_num, gid=gid_num)
        if not os.path.exists(authorized_keys):
            with open(authorized_keys, "w", encoding="utf-8") as auth_key_wp:
                auth_key_wp.write(pub_keys)
            os.chown(authorized_keys, uid=uid_num, gid=gid_num)
            os.chmod(authorized_keys, 0o600)
    return 0                    # OK

def add_user_to_group(info, extra_group):
    """
    add user to group
    """
    key = f'cn={extra_group},ou=groups,{info["ldap_domain"]}'
                # .format(extra_group=extra_group, **info)
    filt = f'(memberUid={info["user"]})'# .format(**info)
    def gen_ldif():
        ldif = f'''dn: cn={extra_group},ou=groups,{info["ldap_domain"]}
changetype: modify
add: memberUid
memberUid: {info["user"]}'''
                # .format(extra_group=extra_group, **info)
        return ldif
    return add_attr_val_ldif(info["ldap_domain"], info["ldap_passwd"],
                             key, filt, gen_ldif, info)

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
    key = f'cn={info["grp"]},ou=groups,{info["ldap_domain"]}' # .format(**info)
    return del_key_if_exist(info["ldap_domain"], info["ldap_passwd"], key, info)

def deluser(info):
    """
    delete user given in info
    """
    key = f'uid={info["user"]},ou=people,{info["ldap_domain"]}'# .format(**info)
    return del_key_if_exist(info["ldap_domain"], info["ldap_passwd"], key, info)

def get_default_ldap_domain():
    """
    get ldap domain
    """
    pat = re.compile("^base +(?P<dom>.*)$")
    with open("/etc/ldap.conf", encoding="utf-8") as conf_fp:
        for line in conf_fp:
            matched = pat.match(line)
            if matched:
                return matched.group("dom")
    return ""

def get_default_ldap_passwd_really():
    """
    get ldap passwd
    """
    with open("/etc/ldap.secret", encoding="utf-8") as pwd_fp:
        return pwd_fp.read()

def get_default_ldap_passwd():
    """
    get ldap passwd
    """
    return "$(cat /etc/ldap.secret)"
