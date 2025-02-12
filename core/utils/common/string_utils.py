import re

def split_string_by_utf8_length(s, max_length, encoding='utf-8', max_split=-1):
    encoded = s.encode(encoding)
    parts = []
    split_count = 0
    while encoded:
        if max_split != -1 and split_count >= max_split:
            parts.append(encoded.decode(encoding))
            break
        part = encoded[:max_length]
        while True:
            try:
                part.decode(encoding)
                break
            except UnicodeDecodeError:
                part = part[:-1]
        parts.append(part.decode(encoding))
        encoded = encoded[len(part):]
        split_count += 1
    return parts

def remove_markdown_symbol(text):
    md_chars = r'*_~`#<>[]{}\|'
    return re.sub(f'[{re.escape(md_chars)}]', '', text) 