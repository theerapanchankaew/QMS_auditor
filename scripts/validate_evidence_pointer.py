#!/usr/bin/env python3
"""Validate the professional-auditor evidence pointer format."""
import json
import re
import sys

PATTERN = re.compile(r"^(?P<clause>[^|]+)\|DOC:(?P<doc>[^|]+)\|TYPE:(?P<type>[^|]+)\|PAGE:(?P<page>[^|]+)\|LINE:(?P<line>[^|]+)\|SECTION:(?P<section>[^|]+)\|SOURCE:(?P<source>[^|]+)$")


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_evidence_pointer.py '<pointer>'", file=sys.stderr)
        return 2
    pointer = sys.argv[1]
    m = PATTERN.match(pointer)
    if not m:
        required = ["clause", "DOC", "TYPE", "PAGE", "LINE", "SECTION", "SOURCE"]
        print(json.dumps({"valid": False, "required_fields": required}, indent=2))
        return 1
    print(json.dumps({"valid": True, "fields": m.groupdict()}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
