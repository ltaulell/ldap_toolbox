#!/usr/bin/env python3
# coding: utf-8
#
# $Id: search_invalid.py 4019 2023-04-18 13:03:09Z ltaulell $
#

"""
Affiche les comptes invalides:
    uid (login), uidNumber, cn, mail

    recherche:
        loginShell

    précision:
        -u = print uid (login) uniquement
        -g = dans un group précis (gidNumber only)
        See dict-ENSL.yml for gidNumber => group

TODO rechercher aussi sur shadowExpire
        avec date du jour par défaut
        ou avec une date fournie (voir shadow_expire.py pour calcul de date)

"""

import argparse
import sys
from pprint import pprint
import yaml

import ldap3


LDAPDICT = 'ldap_psmn.yml'


def main():
    args = get_args()

    if args.d:
        debug = True
        pprint(args)
        print(type(args))
    else:
        debug = False

    if debug:
        searchAttribute = ['objectClass', '*', '+']  # get everything available
    else:
        searchAttribute = ['uid', 'uidNumber', 'gidNumber', 'cn', 'mail']
        # add manager? (/!\ list)

    if args.g:
        # gidNumber = str(args.g[0])
        # searchFilter = ''.join(['(&', '(loginShell=/bin/false)', '(gidNumber=', gidNumber, ')', ')'])
        # rechercher par group litéral ou int : lph vs 2021
        filtre = whatis(args.g[0], debug=debug)
        searchFilter = ''.join(['(&', '(loginShell=/bin/false)', filtre, ')'])
    else:
        searchFilter = ''.join(['(&', '(loginShell=/bin/false)', ')'])

    basedn = 'ou=people'
    bordel = get_ldap_entries(LDAPDICT, basedn, searchFilter, searchAttribute, debug=debug)
    if debug:
        pprint(bordel)
    else:
        for entrie in bordel:
            if args.u:
                print('{}'.format(entrie.uid.value))
            else:
                print('{}, {}, {}, {}'.format(entrie.uid.value, entrie.uidNumber.value, entrie.cn.value, entrie.mail.value))


def whatis(totest, debug=False):
    """
        si (gid == int), gid -> gidNumber, sinon (cn == str), cn,ou=group -> gidNumber
    try:
        x = int(args.gid)
    except ValueError:
        ... do something else ...
    else:
        ... do something with x ...
    """
    try:
        # filtre = '(&(gidNumber=' + args.gid + '))'
        toto = int(totest)
        chaine = '(gidNumber=' + str(toto) + ')'

    except ValueError:
        # filtre = '(&(cn=' + args.gid + '))'
        if debug:
            print("value error -> str, searching gidNumber")
        toto = str(totest)
        basedn = 'ou=group'
        attributes = ['gidNumber']
        filtre = '(&(cn=' + toto + '))'
        liste = get_ldap_entries(LDAPDICT, basedn, filtre, attributes, debug=debug)
        if debug:
            pprint(liste)
        for entrie in liste:  # shouldn't be liste[0] ?
            if debug:
                pprint(entrie.gidNumber.value)
            chaine = '(gidNumber=' + str(entrie.gidNumber.value) + ')'

    return chaine


def get_ldap_entries(ldapDict, searchBase, searchFilter, searchAttribute, debug=False):
    """
    liste = get_ldap_entries('ldap.yml', basedn, filtre, attributes)
        connection to LDAP
        ask searchFilter = '(&(uid=*))'
        read (searchAttribute = ['objectClass', '*', '+'] or ['cn', 'mailRoutingAddress', 'mail'])
        search_scope=BASE|LEVEL|SUBTREE (from ldap3)
        return list of entries (as ldap3.dict)
    """
    ldap_dict = load_yaml_file(ldapDict)
    server = ldap3.Server(ldap_dict['host'], get_info=ldap3.ALL, use_ssl=True)

    # searchLeaf: we search in ou=people OR in ou=group, so 'basedc'
    searchLeaf = searchBase + ',' + ldap_dict['basedc']

    try:
        with ldap3.Connection(server, ldap_dict['who'], ldap_dict['cred'], read_only=True, auto_range=True, raise_exceptions=True) as conn:
            conn.search(searchLeaf, searchFilter, search_scope=ldap3.SUBTREE, attributes=searchAttribute, get_operational_attributes=debug)
            return conn.entries
    except ldap3.core.exceptions.LDAPException as error:
        print('Problem with LDAP connection: {}'.format(error))
        sys.exit(1)


def get_args():
    """
        read parser and return args (as args namespace)
    """
    parser = argparse.ArgumentParser(description="Search for invalidate user(s) in ldap's PSMN")
    parser.add_argument('-d', action='store_true', help='toggle debug ON')
    parser.add_argument('-u', action='store_true', help='only print uid (login)')
    parser.add_argument('-g', nargs=1, help='group (cn or gidNumber, default to all groups)')
    args = parser.parse_args()

    return args


def load_yaml_file(yamlfile):
    """ Load yamlfile, return a dict

    yamlfile is mandatory, using safe_load
    Throw yaml errors, with positions, if any, and quit.
    return a dict
    """
    try:
        with open(yamlfile, 'r') as fichier:
            contenu = yaml.safe_load(fichier)
            return contenu
    except IOError:
        print('Unable to read/load config file: {}'.format(fichier.name))
        sys.exit(1)
    except yaml.MarkedYAMLError as erreur:
        if hasattr(erreur, 'problem_mark'):
            mark = erreur.problem_mark
            msg_erreur = "YAML error position: ({}:{}) in ".format(mark.line + 1,
                                                                   mark.column)
            print(msg_erreur, str(fichier.name))
        sys.exit(1)


if __name__ == "__main__":
    main()
