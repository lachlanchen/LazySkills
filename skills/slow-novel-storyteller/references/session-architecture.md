# Durable Session Architecture

## State Boundary

Keep a transactional store for chapters, paragraphs, jobs, sessions, author notes, and events. Enforce one chapter start per configured local calendar day with a database query and uniqueness logic. Persist after every accepted paragraph.

## Role Threads

Store one thread ID per role: novelist, whole-story critic, prose critic, and translator. Resume the role's own thread on later calls. A single critic may cover both gates for a modest project, but keep the prompts and artifacts distinct. If resume fails, clear only that role and start a new thread with:

- source-authority manifest;
- author core and story promise;
- accepted chapter summaries;
- current chapter contract and prose;
- latest unapplied author notes.

Do not pretend two threads share hidden memory. Their communication is the explicit artifact passed by the controller.

## Small Action State Machine

```text
chapter contract
  for each paragraph
    novelist candidate
    whole-story gate
    prose gate
    while rejected and attempts remain
      novelist rewrite from exact findings
      repeat both relevant gates
    translator draft
    translation gate/revision
    persist accepted bilingual paragraph
    render current reader PDF
  chapter continuity summary
  final render and atomic share sync
```

Record running jobs before external calls. On process restart, return orphaned running jobs to the queue and resume from accepted state. Author notes arriving during a call remain pending for the following paragraph.

Persist every candidate and each gate result separately. Never rely on one thread remembering another thread's finding. Install prose only from an explicit acceptance artifact that identifies the accepted candidate and both source-language gate results.

Use event streams or WebSockets for UI updates. Keep periodic traffic only as a low-frequency reconnect fallback; the durable database remains authoritative after network loss.
