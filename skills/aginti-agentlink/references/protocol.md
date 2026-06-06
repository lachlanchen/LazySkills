# AgInTi AgentLink Protocol

AgInTi AgentLink is a portable collaboration protocol for agent sessions that need to coordinate across machines, repos, devices, and APIs.

## Naming

Recommended skill name:

```text
aginti-agentlink
```

Rationale:

- `AgInTi` aligns with the user's agent system and brand.
- `AgentLink` is clearer than `AgentMesh` for pairwise and small-team coordination.
- Mesh behavior emerges when multiple AgentLinks connect several peer nodes.

Alternative names considered:

```text
AgentMesh
SessionBridge
AgentRelay
ContextLink
AgInTi Constellation
```

`AgInTi AgentLink` is the best default because it is short, brandable, and technically precise.

## Protocol Objects

### Agent node

```json
{
  "id": "windows-codex",
  "host": "CSG1175-P",
  "address": "192.168.1.166",
  "user": "Administrator",
  "workspace": "C:\\Users\\Administrator\\Projects",
  "role": "Arduino USB control and repo editing",
  "tools": ["powershell", "git", "gh", "arduino-cli", "ssh"],
  "constraints": ["Arduino has no IP", "do not commit private session mirrors"]
}
```

### Agent link

```json
{
  "from": "windows-codex",
  "to": "kv260-codex",
  "transport": ["ssh", "http-api", "git"],
  "handoff_docs": ["AGENTS.md", "references/windows-arduino-codex-handoff.md"],
  "private_context": ["private/kv260-codex-history/kv260-history.jsonl"],
  "status_probes": ["ping", "api status", "git status", "device owner"]
}
```

### Action contract

```json
{
  "objective": "Record event-camera response while Arduino modulates LEDs",
  "owner": {
    "windows-codex": ["Arduino upload", "LED modulation", "call KV260 API"],
    "kv260-codex": ["event-camera API", "/dev/video0", "recording files"]
  },
  "allowed_actions": [
    "start KV260 API",
    "compile Arduino sketch",
    "upload Arduino sketch",
    "start recording",
    "stop recording",
    "download results"
  ],
  "stop_conditions": [
    "Arduino board not detected",
    "/dev/video0 busy and takeover not allowed",
    "network unreachable",
    "unexpected dirty worktree"
  ],
  "evidence": [
    "commit hash",
    "API JSON response",
    "recording path",
    "manual hardware observation"
  ]
}
```

## Standard Workflow

### 1. Discover peers

Collect:

```text
hostname
IP address
username
workspace path
repo path
branch
remote
role
available transports
hardware ownership
```

### 2. Read curated memory

Priority:

```text
AGENTS.md
skills/<name>/SKILL.md
docs/*handoff*
docs/*control*
README.md
```

### 3. Probe live state

Examples:

```bash
hostname
ip -4 addr show scope global
git status --short --branch
git remote -v
```

Windows PowerShell:

```powershell
hostname
Get-NetIPAddress -AddressFamily IPv4
arduino-cli board list
```

Remote SSH:

```powershell
ssh.exe user@host "hostname; ip -4 addr show scope global"
```

HTTP API:

```powershell
Invoke-RestMethod "http://host:port/api/v1/status"
```

### 4. Mirror private history only when needed

Rules:

```text
store under private/ or .agentlink/private/
gitignore the folder before or immediately after copying
copy metadata and summary into tracked docs
never commit raw history
```

PowerShell example:

```powershell
$privateDir = "private/peer-history"
New-Item -ItemType Directory -Force -Path $privateDir | Out-Null
ssh.exe user@host "base64 /path/to/history.jsonl" | Set-Content "$privateDir/history.b64" -Encoding ASCII
$b64 = (Get-Content "$privateDir/history.b64" -Raw) -replace '\s+', ''
[IO.File]::WriteAllBytes("$privateDir/history.jsonl", [Convert]::FromBase64String($b64))
Remove-Item "$privateDir/history.b64"
```

### 5. Summarize, do not dump

Tracked summary should include:

```text
source path
local private mirror path
line count
session count
relevant themes
decision rules
search commands
```

### 6. Execute only owned actions

Do not let one agent silently perform actions owned by another machine/session unless the transport and permission are explicit.

Examples:

```text
Windows owns Arduino USB serial.
KV260 owns /dev/video0.
GitHub owns remote push state.
```

### 7. Verify and return evidence

Good evidence:

```text
git commit hash
git push result
API JSON response
recording file path
board list output
device owner output
manual observation recorded in docs
```

## Example: Windows Arduino and KV260 event camera

Peer map:

```text
Windows:
  host: CSG1175-P
  IP: 192.168.1.166
  role: Arduino USB control
  repo: C:\Users\Administrator\Projects\DualLampHI

KV260:
  host: xilinx-kv260-starterkit-20222
  IP: 192.168.1.250
  role: Prophesee event-camera recording
  API: http://192.168.1.250:8765
```

Action split:

```text
Windows:
  arduino-cli board list
  compile/upload sketch
  start/stop LED modulation
  call KV260 API

KV260:
  own /dev/video0
  run recording API
  write .pse2.raw and .json metadata
```

Status probes:

```powershell
arduino-cli board list
Invoke-RestMethod "http://192.168.1.250:8765/api/v1/status"
ssh.exe petalinux@192.168.1.250 "fuser -v /dev/video0 2>/dev/null || true"
```

## AgInTi integration idea

For AgInTi, model AgentLink as a first-class feature:

```text
aginti agentlink init
aginti agentlink peers
aginti agentlink probe <peer>
aginti agentlink handoff write
aginti agentlink mirror-history <peer> --private
aginti agentlink contract run
```

Internal objects:

```text
PeerProfile
ReachabilityProbe
HandoffPacket
PrivateMirror
ActionContract
EvidenceBundle
```

This allows AgInTi to coordinate specialized agents without relying on fragile chat memory.

