#!/usr/bin/env python3

""" Script to get google_project_iam_member fields from tf documents

Run it in a virtual environment: 
    > python3 -m venv env
    > source env/bin/activate
    > pip install python-hcl2
    > chmod +x tf_creds_parser.py
    > ./tf_creds_parser.py gcp_resources.tf


Author: Konstantin N <pardusurbanus@protonmail.com>

"""

import hcl2
import csv
import argparse
import sys
from pathlib import Path

obj_list = None

def csv_map(data_tuple: tuple) -> dict:
    '''
        Create mapping for the csv file
    '''
    idx, el = data_tuple
    el = list(el['google_project_iam_member'].items())[0][1]
    print(el)
    return {
        'No': idx,
        'role': el['role'],
        'member': el['member'],
    }



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("tf_path", help="path to the tf file")
    args = parser.parse_args()

    if not args.tf_path:
        print('No filename given')
        sys.exit(1)

    if not Path(args.tf_path).is_file() or not args.tf_path.endswith('.tf'):
        print(f'{args.tf_path} is bad terraform resource file, please check the path.')
        sys.exit(1)

    with open(str(args.tf_path), 'r') as file:
        try:
            file_dict = hcl2.load(file)
        except Exception:
            print('Error on loading .tf file. Please check the syntax')
            sys.exit(1)

        obj_list = list(filter(
            lambda x: 'google_project_iam_member' in x,
            file_dict['resource']
        ))

    new_dict = list(map(csv_map, enumerate(obj_list)))

    csv_name = str(args.tf_path).replace('.tf','.csv')
    with open(csv_name, 'w') as csv_file:
        fieldnames = ['No', 'role', 'member']

        try:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(new_dict)

            print(f'Finished. Check {csv_name}')
        except Exception:
            print(
                'Cannot write to the csv file. Tried: '
                f'{csv_name}'
                'Please check access rights.'
            )
            sys.exit(1)

