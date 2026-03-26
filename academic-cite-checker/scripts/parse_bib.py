#!/usr/bin/env python3
"""
Parse BibTeX file and extract entries
"""
import sys
import re
import json

def parse_bib_file(content):
    """Parse BibTeX content and return list of entries"""
    entries = []

    # Pattern to match @type{key, ... }
    pattern = r'@(\w+)\s*\{\s*([^,]+),\s*([^}]+)\}'

    # Alternative: handle nested braces
    # Split by @ but keep the delimiter
    parts = re.split(r'(@\w+\s*\{)', content)

    current_entry = None
    for i, part in enumerate(parts):
        if re.match(r'@\w+\s*\{', part):
            # Start of new entry
            match = re.match(r'@(\w+)\s*\{', part)
            if match:
                entry_type = match.group(1)
                # Get the rest
                rest = parts[i+1] if i+1 < len(parts) else ''
                # Find the closing brace
                brace_count = 1
                content_start = 0
                for j, char in enumerate(rest):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found the end
                            entry_content = rest[:j]
                            # Extract key
                            key_match = re.match(r'\s*([^,]+),\s*(.*)', entry_content, re.DOTALL)
                            if key_match:
                                entry_key = key_match.group(1).strip()
                                fields_content = key_match.group(2)

                                # Parse fields
                                fields = parse_fields(fields_content)
                                fields['ENTRY_TYPE'] = entry_type
                                fields['ENTRY_KEY'] = entry_key
                                entries.append(fields)
                            break

    return entries

def parse_fields(content):
    """Parse BibTeX fields from content"""
    fields = {}

    # Pattern: field = {value} or field = "value" or field = value
    # Handle nested braces
    i = 0
    while i < len(content):
        # Skip whitespace and comments
        while i < len(content) and content[i] in ' \t\n\r':
            i += 1

        if i >= len(content):
            break

        # Find field name
        field_start = i
        while i < len(content) and content[i] not in '= \t\n\r':
            i += 1
        field_name = content[field_start:i].strip().lower()

        # Skip to equals sign
        while i < len(content) and content[i] != '=':
            i += 1

        if i >= len(content):
            break

        i += 1  # Skip equals

        # Skip whitespace
        while i < len(content) and content[i] in ' \t\n\r':
            i += 1

        if i >= len(content):
            break

        # Parse value
        value = ''
        if content[i] == '{':
            # Braced value
            brace_count = 1
            i += 1
            value_start = i
            while i < len(content) and brace_count > 0:
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                i += 1
            value = content[value_start:i-1]
        elif content[i] == '"':
            # Quoted value
            i += 1
            value_start = i
            while i < len(content) and content[i] != '"':
                value += content[i]
                i += 1
            i += 1  # Skip closing quote
            value = content[value_start:i-1]
        else:
            # Simple value (until comma or end)
            value_start = i
            while i < len(content) and content[i] != ',':
                i += 1
            value = content[value_start:i].strip()

        # Clean up value
        value = value.replace('\n', ' ').replace('\t', ' ')
        while '  ' in value:
            value = value.replace('  ', ' ')

        fields[field_name] = value.strip()

        # Skip comma
        if i < len(content) and content[i] == ',':
            i += 1

    return fields

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_bib.py <bib_file>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        content = f.read()

    entries = parse_bib_file(content)
    print(json.dumps(entries, indent=2, ensure_ascii=False))
