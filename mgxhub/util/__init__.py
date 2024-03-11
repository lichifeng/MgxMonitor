import string

def sanitize_playername(rawname: str) -> str:
    '''Remove unprintable ASCII characters and strip whitespace from players' names.'''

    return ''.join(c for c in rawname if c in string.printable or ord(c) >= 0x80).strip()