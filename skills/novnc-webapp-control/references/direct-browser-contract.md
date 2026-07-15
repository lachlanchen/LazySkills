# Direct Browser Contract

## Isolation Checklist

Choose non-conflicting values for:

| Resource | Example |
| --- | --- |
| X display | `:96` |
| VNC | `127.0.0.1:5916` |
| noVNC | `127.0.0.1:6116` |
| Chrome CDP | `127.0.0.1:9466` |
| App | `127.0.0.1:4412` |
| Profile | `$XDG_CACHE_HOME/<app>-browser` |

Check listeners and X sockets before launch. A port occupied by an unknown process is a blocker, not permission to kill it.

## Stable UI Surface

First-party applications should expose stable markers such as:

```html
<main data-testid="workspace" data-status="ready">
<textarea data-testid="chat-input"></textarea>
<button data-testid="chat-send">Send</button>
<section data-testid="job" data-status="running"></section>
```

Selectors should encode semantic ownership, not generated class names, DOM depth, or screen coordinates. Coordinates remain a last resort for third-party canvases.

## Evidence Packet

Every meaningful operation should be able to report:

```json
{
  "url": "http://127.0.0.1:4412/",
  "title": "Example Studio",
  "view": "write",
  "selectedDocument": "Example story",
  "jobStatus": "done",
  "screenshot": ".runtime/browser-evidence/<timestamp>-operation.png"
}
```

For a failure, include the current URL, visible state, screenshot, attempted action, timeout, and whether retrying could duplicate a paid action.

## Retry Rules

- Navigation or rendering failure: reload or reopen the same tab, then revalidate identity.
- Missing selector in a first-party app: inspect and improve the app with a stable semantic marker.
- Asynchronous job still running: continue polling the visible state; do not resubmit.
- Job failed before external submission: preserve evidence, fix the general defect, and retry once.
- Login, CAPTCHA, credits, or external confirmation: stop with visible evidence and ask the user only when necessary.
- Unknown outcome after a paid click: never click again until external state proves no job was created.

## Visual Validation

Inspect screenshots at desktop and mobile sizes when layout changes. Confirm that the active controls, status, chat transcript, and confirmation text are visible, non-overlapping, and readable. DOM assertions alone do not catch clipped or covered controls.

## Artifact Identity

Pages may contain tutorials, promotional videos, stale results, hidden preload media, and the current generated artifact at the same time. A page-wide query such as `document.querySelectorAll("video")` is therefore insufficient.

Before accepting a generated artifact:

1. Find the current job or result container from visible workflow state.
2. Locate its preview and download control inside that container.
3. Download once through the visible result action when possible.
4. Probe the file independently and compare duration, dimensions, type, and size with the request.
5. Reject mismatches and preserve evidence; do not copy, publish, or report them as complete.

For media workflows, pass expected duration to the watcher and use a documented tolerance. Hash the accepted source and every copied destination when exact identity matters.
