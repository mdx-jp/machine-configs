# LDAPサーバの設定

## 目的

* 全ホストに共通のユーザ, グループを作る. どのマシンからでも
```
id u10000
```
```
su u10000
```
みたいなことができる

* ユーザが自分で(一回のコマンドで全ホストの)パスワードを変更できる
```
passwd
```

* ドメイン名を設定する

* 管理者パスワードを設定する

## 参考ページ

色々探し回った挙句, 以下が一番, 単刀直入答えに近い感じ

* https://computingforgeeks.com/how-to-configure-ubuntu-as-ldap-client/
* https://computingforgeeks.com/install-and-configure-openldap-server-ubuntu/


まずはこれに沿ってやってみる

## サーバ

### apt

* apt でLDAPを入れるとインタラクティブに色々聞いてくるので, まずはそれに身を委ねてみる

```
sudo apt slapd
```

聞かれた質問とその答え

```
Administrator password = hoge
```

* なおこの時点で dc=nodomain というサブツリー(ドメイン?)が勝手に作られている
* これを知らないとクライアントをどう設定していいかはわからない

```
$ sudo slapcat 
dn: dc=nodomain
objectClass: top
objectClass: dcObject
objectClass: organization
o: nodomain
dc: nodomain
structuralObjectClass: organization
entryUUID: ac681b5a-acc4-103b-9dc2-61c59c65c4fd
creatorsName: cn=admin,dc=nodomain
createTimestamp: 20210918120700Z
entryCSN: 20210918120700.699982Z#000000#000#000000
modifiersName: cn=admin,dc=nodomain
modifyTimestamp: 20210918120700Z

dn: cn=admin,dc=nodomain
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: admin
description: LDAP administrator
userPassword:: e1NTSEF9NmwwRW53WDFsVUFSWmZPaXRLR0pnZ2pWd3hLYkd1VUY=
structuralObjectClass: organizationalRole
entryUUID: ac685a52-acc4-103b-9dc3-61c59c65c4fd
creatorsName: cn=admin,dc=nodomain
createTimestamp: 20210918120700Z
entryCSN: 20210918120700.701618Z#000000#000#000000
modifiersName: cn=admin,dc=nodomain
modifyTimestamp: 20210918120700Z
```

### group, user のサブツリーを作る

以下のファイルを適当なファイル名 (basedn.ldif) で保存し
```
dn: ou=people,dc=nodomain
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=nodomain
objectClass: organizationalUnit
ou: groups
```

```
$ ldapadd -x -D cn=admin,dc=nodomain -w hoge -f basedn.ldif
```

`-w hoge` は apt 時に設定した Administrator password

### groupをひとつ作る

例えばこんなファイルを適当な名前(g10000.ldif)で保存し, 
```
dn: cn=g10000,ou=groups,dc=nodomain
objectClass: posixGroup
cn: g10000
gidNumber: 10000
```

```
sudo ldapadd -x -D cn=admin,dc=nodomain -w hoge -f g10000.ldif
```

### userをひとつ作る

パスワードをハッシュするコマンド(以下は安易にパスワードを u10000 としている)

```
$ slappasswd -s u10000
{SSHA}QZkycx9WyvSMui8R0h7c/qBVjK00sZNO
```

これを元に以下のようなファイルを作り適当な名前(u10000.ldif)に保存

```
dn: uid=u10000,ou=people,dc=nodomain
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
cn: u10000
sn: u10000
userPassword: {SSHA}QZkycx9WyvSMui8R0h7c/qBVjK00sZNO
loginShell: /bin/bash
uidNumber: 10000
gidNumber: 10000
homeDirectory: /home/u10000
```
```
$ sudo ldapadd -x -D cn=admin,dc=nodomain -w hoge -f u10000.ldif
```

## クライアント

### apt

```
apt install libnss-ldap libpam-ldap ldap-utils
```

もれなくインストールされる `ldap-auth-config` の中で聞かれることに対して以下のように答える

```
LDAP server Uniform Resource Identifier: ldap://ikura000/
## ikura000 はサーバの名前. /etc/hosts に書いておかないとダメ. また, ldapi -> ldap と変更しないといけないので注意
Distinguished name of the search base: dc=nodomain
LDAP version to use: 3
LDAP account for root: cn=admin,dc=nodomain
LDAP root account password: hoge
```

* LDAP account for rootは, サーバの方で設定したものを答えないといけないと思うのだが確信はない.
* LDAP root account password はサーバのAdministrator パスワード

* LDAP root account password 以外の設定は /etc/ldap.conf に書かれるから後でも簡単に変更できそう
* LDAP root account password は /etc/ldap.secret に平文で書かれる

### /etc/nsswitch.conf

以下の 2行
```
passwd:         files systemd
group:          files systemd
```
を以下のように変更
```
passwd:         files systemd ldap
group:          files systemd ldap
```

## テスト

### id

```
$ id u10000
uid=10000(u10000) gid=10000(g10000) groups=10000(g10000)
```
* なお, LDAP root account password を間違えてもこれは成功する

### su

```
$ su u10000
password: <- 設定した u10000を入力
```

* なお, こっちはLDAP root account password を間違えると失敗する

## ユーザによるpassword変更

* 以下で, 古いパスワード u10000 を x10000 に変更できた

```
ldappasswd -H ldap://ikura000/ -x -D uid=u10000,ou=people,dc=nodomain -w u10000 -a u10000 -s x10000
```

* しっかしユーザがパスワード一つ変更するのにこんなことをしなくてはいけないのでしょうか

* passwd コマンドで変更できるのかもという淡い期待を持ってやると

```
$ passwd
Enter login(LDAP) password:   <--- x10000 を入力
passwd: Authentication information cannot be recovered
passwd: password unchanged
```

* LDAPパスワードを入れろと言われるのでLDAPのパスワードを変更しようとはしている雰囲気で希望が持てるが, そのユーザのパスワードを入れてもダメ

* ただし他のパスワードを入れると

```
$ passwd
Enter login(LDAP) password: 
LDAP Password incorrect: try again
```

となるので, ユーザのパスワードを入れるところまでは正しい模様

* ググるとこれ https://ubuntuforums.org/showthread.php?t=1640070 が見つかって, `/etc/pam.d/common-password` から use_authtok を取り除けという, https://computingforgeeks.com/how-to-configure-ubuntu-as-ldap-client/ にもある指示だった.

* これで無事, `passwd` コマンドでパスワードの変更が可能になった!!

# 未解決事項

* apt が勝手に作ってくれる nodomain 以外の新しいドメインを, ldapadd で作る方法がわからない
  * slapadd で作ることは可能
  * ldapadd でやろうとすると権限がないとか, よくわからないエラーメッセージが出る
* apt が勝手に作ってくれる nodomain 以外の新しいドメインを消す方法がわからない
  * ldapdelete でやろうとすると権限がないとか, よくわからないエラーメッセージが出る

## Ansibleで自動化

### inventory

* masterとそれ以外で異なる設定が必要なので, 例えば以下のようにする

```
# there must be one server
[master]
2001:2f8:1041:208:250:56ff:feb0:bf5 hostname=ikura000

[server]
2001:2f8:1041:208:250:56ff:feb0:bf7 hostname=ikura001
2001:2f8:1041:208:250:56ff:feb0:bf9 hostname=ikura002
2001:2f8:1041:208:250:56ff:feb0:bfb hostname=ikura003
   ...

[master:vars]
ldap_domain_short=myldap
ldap_domain_pw=foobar

[all:vars]
ansible_user=mdxuser
ldap_domain=dc=myldap,dc=mdx,dc=jp 
ldap_root_pw=hoge
```

* ldap_domainでLDAPのドメイン名を指定する
* ldap_root_pwでLDAP Administrator のパスワードを指定する
  * さしあたり平文にしているが後に変更

### master用playbook

* master だけで実行する config を以下みたいにする

```
- name: master-only things
  hosts: master
  become: yes
  gather_facts: False
  tasks:
  - import_tasks: tasks/ldap-server/task.yml
```

* aptでslapd, ldap-utilsをインストール

```
- name: install slapd on master
  apt:
    state: present
    name:
    - slapd
    - ldap-utils
```

* Administrator パスワードを変更
  * jinja2 templateで ldif ファイルを生成して適用しているのだが, template の結果を stdin にしてコマンドを実行したいのだが方法はある?

```
- name: master generates /tmp/change_root_pw.ldif
  template:
    src: templates/change_root_pw.ldif.j2
    dest: /tmp/change_root_pw.ldif

- name: master changes LDAP root pw
  command: ldapadd -Y EXTERNAL -H ldapi:/// -f /tmp/change_root_pw.ldif
```

* ドメインを作る
  * jinja2 templateで ldif ファイルを生成して適用しているのだが, template の結果を stdin にしてコマンドを実行したいのだが方法はある?

```
- name: master generates /tmp/make_domain.ldif
  template:
    src: templates/make_domain.ldif.j2
    dest: /tmp/make_domain.ldif
  
- name: master makes an LDAP domain
  shell: ldapsearch -Y EXTERNAL -H ldapi:/// -s base -b {{ ldap_domain }} || slapadd -l /tmp/make_domain.ldif
```

### クライアント用playbook

* aptでnscd, libnss-ldap, libpam-ldapをインストール
  * nscd -> sssd とすべき? (イマイチ同じものかわからんので nscd入れとく)
```
- name: install LDAP client packages
  apt:
    state: present
    name:
    - nscd
    - libnss-ldap
    - libpam-ldap
```

* /etc/ldap.conf で ドメイン, LDAPサーバ(master)設定
  * 3か所書き換えるのに3つ別のtaskにしないといけない???
```
- name: change base /etc/ldap.conf
  lineinfile:
    path: /etc/ldap.conf
    regexp: "^base (.*)$"
    line:    "base {{ ldap_domain }}"

- name: change uri /etc/ldap.conf
  lineinfile:
    path: /etc/ldap.conf
    regexp: "^uri (.*)$"
    line:    "uri ldap://{{ hostvars[groups['master'][0]].hostname }}/"
    backup: yes

- name: change rootbinddn /etc/ldap.conf
  lineinfile:
    path: /etc/ldap.conf
    regexp: "^rootbinddn (.*)$"
    line:    "rootbinddn cn=admin,{{ ldap_domain }}"
```

* /etc/ldap.secret に LDAP Administrator パスワード設定
```
- name: generate /etc/ldap.secret
  copy:
    dest: /etc/ldap.secret
    content: "{{ ldap_root_pw }}"
    mode: "0600"
    owner: root
    backup: yes
```

* su できるようにするための設定, 
```
- name: change /etc/pam.d/common-password
  lineinfile:
    path: /etc/pam.d/common-password
    backrefs: yes
    regexp: "^password(.*) use_authtok(.*)$"
    line:    'password\1 \2$'
    backup: yes
```

* passwd, group を LDAP使うように /etc/nsswitch.conf を設定
```
- name: enable ldap for passwd in /etc/nsswitch.conf
  lineinfile:
    path: /etc/nsswitch.conf
    backrefs: yes
    regexp: "^passwd:( *)files systemd *$"
    line:    'passwd:\1files systemd ldap'
    backup: yes
    
- name: enable ldap for group in /etc/nsswitch.conf
  lineinfile:
    path: /etc/nsswitch.conf
    backrefs: yes
    regexp: "^group:( *)files systemd *$"
    line:    'group:\1files systemd ldap'
```

## チェック用コマンド

* slapcat
```
slapcat 
slapcat -n 0
```

* ldapsearch
```
ldapsearch -LLL -x -D cn=admin,dc=myldap,dc=mdx,dc=jp -w rootpw -b dc=myldap,dc=mdx,dc=jp
```
