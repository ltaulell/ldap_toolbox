#!/usr/bin/env python3
# coding: utf-8

# $Id: shadow_expire.py 1294 2020-04-14 15:46:24Z gruiick $
# SPDX-License-Identifier: BSD-2-Clause

""" calcul du shadowExpire
    le champ ldap doit contenir "le nombre de jour depuis le 01/01/1970" ou "-1"

    proto-code, usable as-is:
    je fourni une date, ça me rends un nb de jours depuis 1970
"""

import datetime
DAY0 = datetime.date(1970, 1, 1)

user_input = input("Année-mois-jour : ")

# TODO: verify user input
# print(type(user_input))
# print(user_input)

day1 = datetime.datetime.strptime(user_input, '%Y-%m-%d').date()

# print(type(d1))
# print(d1)

delta = day1 - DAY0
print('shadowExpire: {}'.format(delta.days))

