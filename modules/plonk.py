# Functions to manage a swear jar
import os
import json

misc_path = os.path.join(os.path.curdir, 'data', 'misc')
jar_path = os.path.join(misc_path, 'swearjars.json')

if not os.path.exists(misc_path):
    os.mkdir(misc_path)
if not os.path.exists(jar_path):
    with open(jar_path, 'x') as f:
        f.write('{}')

# Initialize jars
with open(jar_path) as f:
    jars_dict = json.load(f)


def check(user_id: int):
    if str(user_id) not in jars_dict.keys():
        jars_dict[str(user_id)] = [None, 0.0, 0.25]


def get_channel(user_id: int):
    return jars_dict[str(user_id)][0]


def get_quantity(user_id: int):
    return round(jars_dict[str(user_id)][1], 2)


def update(user_id: int):
    jars_dict[str(user_id)][1] += jars_dict[str(user_id)][2]


def set_channel(user_id: int, channel_id: int):
    jars_dict[str(user_id)][0] = channel_id


def set_quantity(user_id: int, quantity: float):
    jars_dict[str(user_id)][1] = round(quantity, 2)


def set_increment(user_id: int, increment: float):
    jars_dict[str(user_id)][2] = increment


def check_word(word: str):
    swears = ['crap', 'shit', 'fuck', 'cunt', 'shitting', 'fucking', 'fucked', 'crapped', 'crapping', 'fucks', 'shits',
              'whore', 'whores', 'whoring', 'bitch', 'bitches', 'bitched', 'bitching', 'ass', 'asses', 'bullshit']
    if word.lower() in swears:
        return True
    else:
        return False


def save():
    with open(jar_path, 'w') as file:
        json.dump(jars_dict, file)
