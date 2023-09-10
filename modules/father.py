# Dad joke helper functions.

# FIXME this is ripped from old Dad. Can't account for "i am" yet.
defense_dict = {
    'i': 'you',
    'i\'m': 'you\'re',
    'im': 'you\'re',
    'i’m': 'you\'re',
    'i`m': 'you\'re, in addition to using weird symbols,',
    'my': 'your',
    'our': 'your',
    'mine': 'your',
    'i\'ve': 'you\'ve',
    'ive': 'you\'ve',
    'i’ve': 'you\'ve',
    'i`ve': 'you\'ve, in addition to used weird symbols,'
}


def triggers_dad(message: str):
    """Returns a boolean depending on whether a given string is food for a dad joke."""
    message = message.lower() + ' '
    if message.startswith('i\'m ') or \
            message.startswith('im ') or \
            message.startswith('i’m ') or \
            message.startswith('i`m ') or \
            message.startswith('i am '):
        return True
    else:
        return False


def parse_name(message: str):
    """Processes a string and gets a name out of its beginning."""
    message = message.lower() + ' '
    # Cut the end of the string off
    # "i'm so tired, time for bed. night!" becomes "i'm so tired" after this
    for c in '.,!?':
        idx = message.find(c)
        if not idx == -1:
            message = message[:idx]+' '
    # Cut the beginnings off
    # "i'm so tired" becomes "so tired" after this
    # "i'm i'm stupid" becomes "stupid" after this
    while message.startswith('i\'m ') or \
            message.startswith('im ') or \
            message.startswith('i’m ') or \
            message.startswith('i`m ') or \
            message.startswith('i am '):
        if message.startswith('i am '):
            message = message[5:].strip() + ' '
        elif message.startswith('im '):
            message = message[3:].strip() + ' '
        else:
            message = message[4:].strip() + ' '
    # TODO is defense necessary? If so, it would go here.
    # Check to see if the result is valid
    if message.strip() == '':
        raise ValueError('Invalid name.')
    for c in '.,!?':
        if message.startswith(c):
            raise ValueError('Invalid name.')
    # Capitalize the name
    name = message.capitalize()
    # Last check: Is the name too long? The dad joke works best with short statements like
    # "I'm tired", "I'm so frustrated", etc. and not "I'm going to harm the developers of this game"
    if len(name[:-1]) > 20:
        raise ValueError('Name too long.')
    # Return name
    return name[:-1]
