# Functions to retrieve settings
import os
import json

settings_path = os.path.join(os.path.curdir, 'data', 'settings')
forbidden_path = os.path.join(settings_path, 'forbidden.json')
logging_path = os.path.join(settings_path, 'logging.json')

if not os.path.exists(settings_path):
    os.mkdir(settings_path)
if not os.path.exists(forbidden_path):
    with open(forbidden_path, 'x') as f:
        f.write('[]')
if not os.path.exists(logging_path):
    with open(logging_path, 'x') as f:
        f.write('{}') # change to whatever an empty dictionary looks like


def forbidden():
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


def logging():
    # Read the forbidden json
    with open(logging_path) as f:
        log_dict = json.load(f)
    return log_dict


def add_logging(guild: int, id: int):
    log_dict = logging()
    guild = str(guild)
    if guild not in log_dict.keys():
        log_dict[guild] = id
    elif log_dict[guild] == id:
        raise IndexError('Already logging this server to this channel.')
    else:
        log_dict[guild] = id
    # Save the updated list
    with open(logging_path, 'w') as f:
        json.dump(log_dict, f)


def clear_logging(guild: int):
    log_dict = logging()
    guild = str(guild)
    if guild not in log_dict.keys():
        raise IndexError('This server was not logged.')
    else:
        del log_dict[guild]
    # Save the updated list
    with open(logging_path, 'w') as f:
        json.dump(log_dict, f)
