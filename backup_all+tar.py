#!/usr/bin/env python3
# coding: utf-8
#
# $Id: backup_all+tar.py 2466 2018-12-12 15:49:55Z ltaulell $
#

"""
    backup du contenu du LDAP 
        recherche/lecture dans le ldap (dc=example,dc=org)
        écriture de la fiche ldif correspondante
    backup de tout ça dans une archive datée

    module ldap3 >= v2.2.4

TODO:
    A TESTER !
    * OK pour uid=*,ou=people
    * OK pour cn=<uid>,ou=auto.home
    * OK pour cn=*,ou=group
    * OK pour archive datée
    * TODO pour cn=*,ou=auto.site
    * TODO pour cn=*,ou=auto.master

    recherche/lecture dans le ldap (ou=*,ou=psmn) ldap3.SUBTREE 
    ou recherche/lecture dans le ldap (cn=*,ou=auto.*,ou=psmn) ?

    optimiser un pneu : 
        * OK : 1 seule ouverture de fichier pour l'écriture des ldif 
        * OK : 1 seule ouverture de l'archive
    https://docs.python.org/3.5/library/io.html#io.StringIO
    https://docs.python.org/3.5/library/io.html

"""

import argparse
import ldap3
import sys
import yaml
import tarfile

from pprint import pprint
from datetime import datetime


def main():
    """ """
    args = get_args()

    today = datetime.now().strftime('%Y-%m-%d')
    if args.d:
        print(today)

    archfile = today + '.tar'
    tf = tarfile.open(archfile, 'a')

    """
        sauvegarde des uid=*,ou=people,dc=example,dc=org
            +cn=<uid>,ou=auto.home,ou=psmn,dc=example,dc=org
    """

    basedn = 'ou=people'
    filtre = '(&(uid=*))'
    liste = getLdapEntries('ldap_psmn.yml', basedn, filtre)

    if args.d:
        print(len(liste),"compte(s)")

    for entry in liste:
        if args.d:
            print(entry.uid)
            #pprint(entry.entry_to_ldif())
        filename=str(entry.uid) + ".ldif"
        result1=str(entry.entry_to_ldif())
        # append auto.home entry to ldif
        basedn = 'ou=auto.home,ou=psmn'
        filtre = '(&(cn=' + str(entry.uid) + '))'
        liste2 = getLdapEntries('ldap_psmn.yml', basedn, filtre)

        for entry2 in liste2:
            if args.d:
                print(entry2.cn)
                #pprint(entry2.entry_to_ldif())
            result2=str(entry2.entry_to_ldif())
        lines = result1 + "\n" + result2
        if args.d:
            pprint(lines)
        if args.w:
            writeFile(filename, lines)
            tf.add(filename)

    """
        sauvegarde des cn=*,ou=group,dc=example,dc=org
    """

    basedn = 'ou=group'
    filtre = '(&(cn=*))'
    liste = getLdapEntries('ldap_psmn.yml', basedn, filtre)

    if args.d:
        print(len(liste),"group(s)")

    for entry in liste:
        if args.d:
            print(entry.cn)
            #pprint(entry.entry_to_ldif())
        filename=str(entry.cn) + ".ldif"
        lines=str(entry.entry_to_ldif())
        if args.w:
            writeFile(filename, lines)
            tf.add(filename)

    """
        On a fini, on range.
    """
    tf.close()


def get_args():
    """ """
    parser = argparse.ArgumentParser(description='Backup PSMN ldap to ldif files.')
    parser.add_argument('-d', action='store_true', help='toggle debug ON')
    parser.add_argument('-w', action='store_true', help='write ldif extracts', required=True)
    # -w est required=True en attendant que je trouve un truc moins crétin

    args = parser.parse_args()
    return args


def loadDict(yamlfile):
    """
        Load data from yamlfile, using safe_load
        yamlfile is mandatory
        return a dict{}
    """
    try:
        with open(yamlfile, 'r') as fichier:
            yamlcontenu = yaml.safe_load(fichier)
            return(yamlcontenu)
    except IOError:
        print("Impossible d'ouvrir le fichier ", fichier.name)
        sys.exit(1)


def writeFile(nom, contenu):
    """
        Write contenu into nom as file
        nom and contenu are mandatory (as str)
    """
    try:
        with open(nom, "wt", encoding="UTF-8") as outputfile:
            for line in contenu:
                outputfile.write(line)
            outputfile.write('\n')  # add empty newline @end
        print(nom + ' OK')
    except IOError:
        print("Impossible d'ouvrir le fichier ", outputfile.name)
        sys.exit(1)


def getLdapEntries(ldapDict, searchBase, searchFilter):
    """
        connection to LDAP
        search
        return list of entries (as ldap3.dict)
    """
    ldap_dict = loadDict(ldapDict)
    server = ldap3.Server(ldap_dict['host'], get_info=ldap3.ALL, use_ssl=True)
    #searchAttribute = ['objectClass', '*', '+']
    searchAttribute = ['objectClass', '*']
    searchLeaf = searchBase + ',' + ldap_dict['basedc']
    #search_scope=BASE|LEVEL|SUBTREE (from ldap3)

    try:
        with ldap3.Connection(server, ldap_dict['who'], ldap_dict['cred'], read_only=True, auto_range=True, raise_exceptions=True) as conn:
            conn.search(searchLeaf, searchFilter, search_scope=ldap3.SUBTREE, attributes=searchAttribute, get_operational_attributes=False) 
            return conn.entries
    except LDAPException as error:
        print("Probleme avec la connexion LDAP:" + error)
        sys.exit(1)


if __name__ == "__main__":
    main()
