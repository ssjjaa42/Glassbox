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
        f.write('{}')

# Initialize settings
with open(forbidden_path) as f:
    forbidden_ids = json.load(f)
with open(logging_path) as f:
    log_dict = json.load(f)


def forbidden():
    return forbidden_ids


def add_forbidden(id: int): 
    if id not in forbidden_ids:
        forbidden_ids.append(id)
    else:
        raise IndexError('The given ID was already on the blacklist.')


def remove_forbidden(id: int):
    if id not in forbidden_ids:
        raise IndexError('The given ID was not on the blacklist.')
    else:
        forbidden_ids.remove(id)


def logging():
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


def clear_logging(guild: int):
    guild = str(guild)
    if guild not in log_dict.keys():
        raise IndexError('This server was not logged.')
    else:
        del log_dict[guild]


def save():
    '''Save settings to their respective files.'''
    with open(forbidden_path, 'w') as f:
        json.dump(forbidden_ids, f)
    with open(logging_path, 'w') as f:
        json.dump(log_dict, f)
