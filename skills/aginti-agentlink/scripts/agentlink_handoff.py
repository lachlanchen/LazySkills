#!/usr/bin/env python3
"""Generate AgInTi AgentLink handoff templates."""

from __future__ import annotations

import argparse
from datetime import date


TEMPLATE = """# AgentLink Handoff

Updated: {today}

## Objective

Describe the shared goal.

## Peers

| Peer | Host | Address | User | Workspace | Role | Reachability |
| --- | --- | --- | --- | --- | --- | --- |
| peer-a |  |  |  |  |  |  |
| peer-b |  |  |  |  |  |  |

## Current State

List facts verified by files, commands, APIs, or device status.

## Tools and APIs

```text
commands:
apis:
scripts:
device paths:
ports:
```

## Ownership Boundaries

```text
peer-a owns:
peer-b owns:
shared:
```

## Action Contract

```text
objective:
allowed actions:
stop conditions:
expected evidence:
```

## Private Context

```text
ignored folders:
private mirrors:
raw histories:
rules:
```

## Evidence

```text
commit hashes:
status outputs:
recording paths:
logs:
manual observations:
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an AgentLink handoff Markdown template.")
    parser.add_argument("--template", action="store_true", help="Print the standard handoff template.")
    args = parser.parse_args()
    if args.template:
        print(TEMPLATE.format(today=date.today().isoformat()))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

