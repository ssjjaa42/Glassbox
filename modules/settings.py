# Functions to retrieve settings
import os
import json

forbidden_path = os.path.join(os.path.curdir, 'data', 'settings', 'forbidden.json')


def forbidden():
    # Make the forbidden json if it doesn't exist yet
    if not os.path.exists(os.path.join(os.path.curdir, 'data', 'settings')):
        os.mkdir(os.path.join(os.path.curdir, 'data', 'settings'))
    if not os.path.exists(forbidden_path):
        with open(forbidden_path, 'x') as f:
            f.write('[]')
    # Read the forbidden json
    with open(forbidden_path) as f:
        forbidden_ids = json.load(f)
    return forbidden_ids


def add_forbidden(id: int):
    forbidden_ids = forbidden()
    if id not in forbidden_ids:
        forbidden_ids.append(id)
    else:
        raise IndexError('The given ID was already on the blacklist.')
    # Save the updated list
    with open(forbidden_path, 'w') as f:
        json.dump(forbidden_ids, f)


def remove_forbidden(id: int):
    forbidden_ids = forbidden()
    if id not in forbidden_ids:
        raise IndexError('The given ID was not on the blacklist.')
    else:
        forbidden_ids.remove(id)
    # Save the updated list
    with open(forbidden_path, 'w') as f:
        json.dump(forbidden_ids, f)
