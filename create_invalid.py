#!/usr/bin/env python3
# coding: utf-8
#
# $Id: create_invalid.py 2789 2020-01-20 13:44:27Z ltaulell $
#

"""
Prépare un ldif d'invalidation (bascule loginShell en '/bin/false')
car adresse email (fournit dans un fichier en argument) est en NPAI.

    * filtrer sur adresse email
        afficher uid, cn, group
        try user.description
            si 'loginShell' != /bin/false
                loginShell = /bin/false
                modify description
            sinon
                afficher le contenu de 'description:'
        except ldap3 Error(s)
            si 'loginShell' != /bin/false
                loginShell = /bin/false
                ajoute description
            sinon
                ajoute description

"""

import argparse
import sys
import datetime
from pprint import pprint
import yaml


import ldap3


LDAPDICT = 'ldap_psmn.yml'


def get_args():
    """ read parser and return args (as args namespace)
    """
    parser = argparse.ArgumentParser(description="Invalidate user(s) in ldap's PSMN")
    parser.add_argument('-d', action='store_true', help='toggle debug ON')
    parser.add_argument('-f', nargs=1, help='entries file (one email adresse by line)', required=True)
    args = parser.parse_args()

    return args


def load_fichier(infile, debug=False):
    """ lit le fichier 'infile'

    retourne le contenu dans une liste
    """
    result = []
    try:
        with open(infile, 'rt', encoding='UTF-8') as fichier:
            result = fichier.readlines()
            if debug:
                print(result)
            return result
    except IOError:
        print("Impossible d'ouvrir le fichier", fichier.name)
        sys.exit(1)


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


def get_ldap_entries(ldapDict, searchFilter, searchAttribute, debug=False):
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

    searchLeaf = ldap_dict['basedn']  # we search in ou=people,...

    try:
        with ldap3.Connection(server, ldap_dict['who'], ldap_dict['cred'], read_only=True, auto_range=True, raise_exceptions=True) as conn:
            conn.search(searchLeaf, searchFilter, search_scope=ldap3.SUBTREE, attributes=searchAttribute, get_operational_attributes=debug)
            return conn.entries
    except ldap3.core.exceptions.LDAPException as error:
        print('Problem with LDAP connection: {}'.format(error))
        sys.exit(1)


def write_ldif(nom, data):
    """ write data (provided as list) into 'nom'.ldif """
    with open(nom + '.ldif', 'w') as fichier:
        fichier.write('\n'.join(data))


if __name__ == "__main__":
    args = get_args()
    debug = args.d
    if debug:
        pprint(args)
        print(type(args))

    timestamp = datetime.datetime.now().strftime('%Y%m%d')
    fichier = str(args.f[0])
    adresses_invalides = load_fichier(fichier, debug=debug)

    searchAttribute = ['objectClass', '*', '+']  # we need everything
    # searchAttribute = ['uid', 'mail', 'loginShell', 'description']  # this is not enought...

    for adresse in adresses_invalides:
        searchFilter = ''.join(['(&(mail=', adresse, '))'])  # adresse.lower() ?
        bordel = get_ldap_entries(LDAPDICT, searchFilter, searchAttribute, debug=debug)

        for user in bordel:
            contenu = []
            dn = 'uid=' + user.uid.value + ',ou=people,dc=flmsn,dc=org'
            chaine = 'invalid {}'.format(timestamp)

            contenu.extend(['version: 1', ''])
            contenu.append(''.join(['dn: ', dn]))
            contenu.append('changetype: modify')

            try:
                print('{}: {}'.format(user.mail, user.description))
                if user.loginShell != '/bin/false':
                    contenu.append('replace: loginShell')
                    contenu.append('loginShell: /bin/false')
                    contenu.append('-')
                    contenu.append('replace: description')
                    contenu.append(''.join(['description: ', chaine]))

                    if debug:
                        pprint(contenu)
                    write_ldif(user.uid.value, contenu)

                    print('\tmettre à jour {} (invalidé)'.format(user.mail))

            except (ldap3.core.exceptions.LDAPKeyError, ldap3.core.exceptions.LDAPCursorError):
                print('{}: {}'.format(user.mail, 'description vide'))
                if user.loginShell != '/bin/false':
                    contenu.append('replace: loginShell')
                    contenu.append('loginShell: /bin/false')
                    contenu.append('-')
                    contenu.append('add: description')
                    contenu.append(''.join(['description: ', chaine]))

                    if debug:
                        pprint(contenu)
                    write_ldif(user.uid.value, contenu)

                    print('\tmettre à jour {} (invalidé)'.format(user.mail))

                else:
                    contenu.append('add: description')
                    contenu.append(''.join(['description: ', chaine]))

                    if debug:
                        pprint(contenu)
                    write_ldif(user.uid.value, contenu)

                    print('\tmettre à jour {} (invalidé)'.format(user.mail))
                # pass
