import re

def split_string_by_utf8_length(s, max_length, encoding='utf-8'):
    encoded = s.encode(encoding)
    parts = []
    while encoded:
        part = encoded[:max_length]
        while True:
            try:
                part.decode(encoding)
                break
            except UnicodeDecodeError:
                part = part[:-1]
        parts.append(part.decode(encoding))
        encoded = encoded[len(part):]
    return parts

def remove_markdown_symbol(text):
    md_chars = r'*_~`#<>[]{}\|'
    return re.sub(f'[{re.escape(md_chars)}]', '', text) 