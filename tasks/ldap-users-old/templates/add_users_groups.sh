# add primary group of all users
for x in {{ ldap_users.list | map(attribute="gid") | join(" ") }} ; do
  if ! ldapsearch -x -D cn=admin,{{ ldap_domain }} -b cn=${x},ou=groups,{{ ldap_domain }} -w {{ ldap_root_password }} > /dev/null ; then
    cat  /tmp/ldap-users/user-group-${x}.ldif ;
  fi ;
done | ldapadd -x -D cn=admin,{{ ldap_domain }} -w {{ ldap_root_password }}

# add all users
for x in {{ ldap_users.list | map(attribute="uid") | join(" ") }} ; do
  if ! ldapsearch -x -D cn=admin,{{ ldap_domain }} -b uid=${x},ou=people,{{ ldap_domain }} -w {{ ldap_root_password }} > /dev/null ; then
    cat  /tmp/ldap-users/user-${x}.ldif ;
  fi ;
done | ldapadd -x -D cn=admin,{{ ldap_domain }} -w {{ ldap_root_password }}
