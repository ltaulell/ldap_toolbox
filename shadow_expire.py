#!/usr/bin/env python3
# coding: utf-8

# $Id: shadow_expire.py 1308 2020-05-06 07:14:43Z gruiick $
# SPDX-License-Identifier: BSD-2-Clause

""" calcul du shadowExpire
    le champ ldap doit contenir "le nombre de jour depuis le 01/01/1970" ou "-1"

    proto-code, usable as-is:
    je fourni une date, ça me rends un nb de jours
"""

import argparse
import datetime


DAY0 = datetime.date(1970, 1, 1)

parser = argparse.ArgumentParser(description='Calculate shadowExpire value')

group1 = parser.add_mutually_exclusive_group(required=False)
group1.add_argument('-v', action='store_true', help='toggle verbosity (debug ON)')
group1.add_argument('-s', action='store_true', help='silent, only return result')

parser.add_argument('date', action='store', nargs='?', type=str, default=None, help='date you want to transform (dd-mm-YYYY)')
args = parser.parse_args()

if args.v:
    print(args)

# TODO: verify user input and accept datetime object
if not args.date:
    user_input = input('Année-mois-jour (dd-mm-YYYY): ')
else:
    user_input = args.date

if args.v:
    print(type(user_input))
    print(user_input)

day1 = datetime.datetime.strptime(user_input, '%d-%m-%Y').date()

if args.v:
    print(type(day1))
    print(day1)

delta = day1 - DAY0

if not args.s:
    print('shadowExpire: {}'.format(delta.days))
else:
    print('{}'.format(delta.days))
