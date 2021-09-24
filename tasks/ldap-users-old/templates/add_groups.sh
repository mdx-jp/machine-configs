for x in {{ ldap_groups.list | map(attribute="gid") | join(" ") }} ; do
    if ! ldapsearch -x -D cn=admin,{{ ldap_domain }} -b cn=${x},ou=groups,{{ ldap_domain }} -w {{ ldap_domain_password }} > /dev/null ; then
        cat /tmp/ldap-users/${x}.ldif ;
    fi ;
done | ldapadd -x -D cn=admin,{{ ldap_domain }} -w {{ ldap_domain_password }}
