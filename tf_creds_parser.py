#!/usr/bin/env python3

""" Script to get google_project_iam_member fields from tf documents

Run it in a virtual environment:
    > python3 -m venv env
    > source env/bin/activate
    > pip install python-hcl2
    > chmod +x tf_creds_parser.py
    > ./tf_creds_parser.py --iam gcp_resources.tf


Author: Konstantin N <pardusurbanus@protonmail.com>
Version: 0.0.3
"""

import hcl2
import csv
import argparse
import sys
from pathlib import Path
import enum
from dataclasses import dataclass, asdict


@dataclass
class BQResource(object):
    '''
        Represents BQ resource access

        ...

        Attributes
        ----------
        no: int
            record number
        dataset_id: str
        role: str
        entity: str
            aceess entity: group, user, view
    '''
    dataset_id: str
    role: str
    entity: str = ''
    no: int = 0


@dataclass
class IAMResource(object):
    '''
        Represents IAM resource access

        ...

        Attributes
        ----------
        no: int
            record number
        role: str
        member: str
            aceess entity (member)
    '''
    role: str
    member: str
    no: int = 0


class Mode(enum.Enum):
    BQ = 1,
    IAM = 2


def list_prepare(mode: Mode, tf_dict: dict) -> list:
    '''Get access entities from tf file dict'''

    resource_dict = tf_dict['resource']
    resource = ''
    if mode == Mode.BQ:
        resource = 'google_bigquery_dataset'
    elif mode == Mode.IAM:
        resource = 'google_project_iam_member'
    else:
        return []

    obj_list = list(map(
        lambda x: list(x[resource].items())[0][1],
        filter(
            lambda x: resource in x,
            resource_dict
        )
    ))

    return obj_list


def csv_iam_map(data_tuple: tuple) -> dict:
    '''Mapping iam resource dict to csv type'''
    idx, el = data_tuple

    obj = asdict(IAMResource(**{
        'no': idx+1,
        'role': el['role'],
        'member': el['member'],
    }))

    print(obj)
    return obj


def csv_bq_map(data_tuple: tuple) -> dict:
    '''Mapping bq resource dict to csv type'''
    idx, el = data_tuple
    el.no = idx+1
    obj = asdict(el)
    print(obj)
    return obj


def bq_parse(els: list) -> dict:
    '''Parsing bq resources'''

    accesses = []

    for el in els['access']:
        if 'view' in el:
            for access in el['view']:
                obj = BQResource(**{
                    'dataset_id': access['dataset_id'],
                    'role': 'view',
                    'entity': access['project_id'],
                })
                accesses.append(obj)
        else:
            obj = BQResource(**{
                'dataset_id': els['dataset_id'],
                'role': el['role'],
            })

            if 'user_by_email' in el:
                obj.entity = el['user_by_email']
            if 'domain' in el:
                obj.entity = el['domain']
            if 'special_group' in el:
                obj.entity = el['special_group']
            if 'group_by_email' in el:
                obj.entity = el['group_by_email']
            accesses.append(obj)

    return accesses


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--iam", action="store_true",
        help="parse iam resources (default)"
    )
    parser.add_argument(
        "-b", "--bq", action="store_true",
        help="parse big query resources"
    )
    parser.add_argument("tf_path", help="path to the tf file")
    args = parser.parse_args()

    curr_mode = Mode.IAM

    if args.bq:
        curr_mode = Mode.BQ

    if args.iam and args.bq:
        print('\nPlease choose either iam or bq option\n')
        parser.print_help()
        sys.exit(1)

    if not args.tf_path:
        print('No filename given')
        sys.exit(1)

    if not Path(args.tf_path).is_file() or not args.tf_path.endswith('.tf'):
        print((
            f'{args.tf_path} is bad terraform '
            'resource file, please check the path.'
        ))
        sys.exit(1)

    file_dict = None

    with open(str(args.tf_path), 'r') as file:
        try:
            file_dict = hcl2.load(file)
        except Exception:
            print('Error on loading .tf file. Please check the syntax')
            sys.exit(1)

    lst = list_prepare(curr_mode, file_dict)

    if curr_mode == Mode.IAM:
        fieldnames = ['no', 'role', 'member']
        new_list = list(map(csv_iam_map, enumerate(lst)))
    else:
        fieldnames = ['no', 'dataset_id', 'role', 'entity']
        new_list = sum(list(map(bq_parse, lst)), [])
        new_list = list(map(csv_bq_map, enumerate(new_list)))

    csv_name = str(args.tf_path).replace('.tf', '.csv')
    with open(csv_name, 'w') as csv_file:

        try:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(new_list)

            print(f'Finished. Check {csv_name}')
        except Exception:
            print(
                'Cannot write to the csv file. Tried: '
                f'{csv_name}'
                'Please check access rights.'
            )
            sys.exit(1)
