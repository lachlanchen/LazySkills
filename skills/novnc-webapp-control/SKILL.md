---
name: novnc-webapp-control
description: Use when opening, controlling, testing, or refining a locally developed webapp through a dedicated Xvfb/noVNC Chrome profile, especially when the user wants visible browser operation, direct DOM manipulation instead of API shortcuts, stable repeatable controls, screenshots, long-running chat workflows, or iterative fixes until the webapp completes its task.
---

# noVNC Webapp Control

Operate the real webapp in an isolated, observable browser. Treat the webapp as the product under test: enter requests through visible controls, observe its own progress UI, and fix the app or controller when the workflow cannot finish.

## Control Contract

- Allocate a dedicated X display, VNC port, noVNC port, CDP port, app port, and Chrome profile. Never reuse an unrelated automation profile.
- Bind VNC, noVNC, CDP, and local app services to `127.0.0.1` unless the user explicitly asks for remote exposure.
- Manipulate the webapp through Playwright/CDP locators and visible controls. Do not replace a failed UI interaction with a direct application API mutation.
- Health probes may check service startup. They are not substitutes for browser actions.
- Reuse one app tab and bring it to the front before every operation.
- Add stable `data-testid` and state attributes to first-party UI when selectors are ambiguous.
- Capture before, after, and failure screenshots plus a machine-readable status summary.
- Require a visible confirmation for paid, destructive, publishing, or irreversible actions. Submit exactly once.
- Scope generated-artifact discovery to the current job or result container. Never accept unrelated media merely because it appears elsewhere on the page.
- Validate downloaded artifacts against the request using available evidence such as duration, dimensions, filename, hash, and visible result identity before copying or reporting success.
- When a first-party app delegates to a second browser service, require the app to establish and report that service's observable noVNC desktop before delegation. A reachable CDP endpoint alone is not visible-operation proof.

## Workflow

1. Inspect the app, existing desktop launchers, browser dependencies, and occupied ports.
2. Define the action contract: target page, expected visible inputs, expected evidence, terminal success states, blockers, and irreversible actions.
3. Instrument the first-party app with stable selectors and explicit state markers where needed.
4. Launch Xvfb, x11vnc, websockify/noVNC, the app server, and Chrome with a dedicated profile.
5. Attach Playwright over CDP. Reuse the target tab, call `bringToFront()`, and verify URL, title, and an app-root marker.
6. Drive the workflow through the UI. For chat tasks, type into the chat composer, click its visible action, and wait for a new assistant message or terminal job state.
7. Validate both DOM state and a visual screenshot. For media output, also probe the downloaded file and compare it with the requested duration or format. A completion claim without evidence is not completion.
8. If blocked, save evidence, classify whether the app, controller, browser, or external service failed, patch the smallest general fix, restart only the affected layer, and retry from the last proven state.
9. Leave the desktop running when the user wants to monitor it and report the exact noVNC URL and profile/port isolation.

## Lala Studio Adapter

From the Lala Studio repository:

```bash
scripts/launch_studio_novnc.sh start --project-root "$LALA_STUDIO_PROJECT_ROOT"
node tools/lala-studio-browser.mjs status
node tools/lala-studio-browser.mjs select-story --match "story title"
node tools/lala-studio-browser.mjs chat --action final --message "Polish this story"
node tools/lala-studio-browser.mjs apply-last
node tools/lala-studio-browser.mjs save
node tools/lala-studio-browser.mjs production \
  --message "Generate this 15 second video" \
  --operation prepare
node tools/lala-studio-browser.mjs delivery \
  --message "Download the current result if needed and publish it with LazyEdit" \
  --operation inspect
```

Use `--operation generate --confirm-paid` only after the user has explicitly requested generation and the visible production contract is correct.

Read [direct-browser-contract.md](references/direct-browser-contract.md) when adding this pattern to another app or diagnosing a failed long-running flow.
