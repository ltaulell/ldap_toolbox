# ldap toolbox

PSMN toolbox aimed at ldap management

## Basic workflows

Each python script work with YAML configuration (one for ldap connection, 
one for groups & volumes definition) files.

* ldap_source.yml:

``` ldap_source.yml
%YAML 1.1
---
host: "sourceldap.example.org"
who: "cn=reader,dc=example,dc=org"
cred: "password"
basedn: "ou=people,dc=example,dc=org"
basedc: "dc=example,dc=org"
```

* ldap_target.yml:

``` ldap_target.yml
%YAML 1.1
---
host: "targetldap.cc.example.org"
who: "cn=writer,dc=cc,dc=example,dc=org"
cred: "password"
basedn: "ou=people,dc=cc,dc=example,dc=org"
basedc: "dc=cc,dc=example,dc=org"
```

* GROUPS_dictionary.yml:

``` GROUPS_dictionary.yml
%YAML 1.1
---
#STRUCT:
#  group: ""
#  gid: ""
#  volume: ""
#  server: ""
FAHome:
  group: "fahome"
  gid: "2001"
  volume: "fahomes"
  server: "dataserv1"
```

### New internal user

3 steps workflow (user exist in databases):

* ask source ldap (or general Information System) for data

use ask_one_2ldif.py 

* verify/modify

use shadow_expire.py to calculate shadowExpire value

use $EDITOR (vim should be perfect)

* push into target ldap

use push_ldif_2target.py

### New external user

2 steps workflow:

* minimal informations in temp.csv

use create_external_2ldif.py

* push into target ldap

use push_ldif_2target.py

## Change SizeLimits

* olcSizeLimit.ldif:

``` olcSizeLimit.ldif
version: 1
  
dn: cn=config 
changetype: modify
replace: olcSizeLimit
olcSizeLimit: 1000
#olcSizeLimit: unlimited

# may do better :
# https://openldap.org/doc/admin24/limits.html
```

## Save as separate LDIF

use backup_all+tar.py


