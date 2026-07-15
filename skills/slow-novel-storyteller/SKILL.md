---
name: slow-novel-storyteller
description: Use when designing, operating, or repairing a high-quality long-form novel workflow that writes slowly by paragraph, limits production to one readable chapter per day, preserves author-written source authority, separates novelist/critic/translator sessions, resumes durably, or publishes clean chapter PDFs.
---

# Slow Novel Storyteller

Build the smallest durable system that protects literary attention. The novelist should receive story and author context, not agent, code, database, TeX, git, or deployment narration.

## Prepare The Inheritance

1. Inventory author drafts, notes, beatboards, personal writing, research, later AI drafts, and current steering.
2. Rank provenance before combining material. Read [source-authority.md](references/source-authority.md).
3. Extract an author core: recurring struggles, pleasures, moral tensions, sense of humor, desired reader experience, and contradictions that must stay alive.
4. Treat copyrighted reading as craft study. Abstract causality, scene scale, dialogue pressure, and structure; never copy phrases, characters, or distinctive plots.

## Separate Roles

Use independent persistent sessions:

- **Novelist:** writes one prose paragraph and accumulates emotional/continuity memory.
- **Critic:** assumes failure is possible, evaluates in whole-story and local context, and returns concrete findings without replacement prose.
- **Translator:** works only from accepted source prose, a glossary, and nearby continuity.

An outer deterministic layer owns schemas, state, retries, files, compilation, version control, and publishing. Pass artifacts explicitly between roles. Read [session-architecture.md](references/session-architecture.md) before implementing resumability.

## Write One Chapter

1. Enforce the daily limit in durable state using a local calendar date, not only in a prompt.
2. Decide only the current chapter's contract and title. Do not freeze every future title.
3. Write one paragraph at a time from the contract, accepted prose, story memory, and newest author note.
4. Run the independent gate in [quality-gates.md](references/quality-gates.md).
5. Return precise criticism to the same novelist session. Allow a bounded number of complete rewrites; block for review rather than accepting a weak final attempt.
6. Translate only after source prose passes. Review the translation for natural target-language prose and factual fidelity.
7. Persist accepted text immediately. Rebuild a current reader artifact, then commit only scoped outputs.
8. Close the chapter only after its promised irreversible turn and immediate aftermath. Save a continuity summary; decide the next chapter on a later day.

## Publish For Reading

- Keep English/source and translated chapter files separate.
- Generate clean pocket PDFs with a cover and readable type.
- Back up the existing owner PDF before changing its LaTeX source.
- Sync atomically and verify checksums.
- Export only reader PDFs to shared folders; keep prompts, databases, logs, TeX, and backups private.

## Completion Check

- Daily limit is tested and survives restart.
- Sessions resume by stable role and can be reseeded from durable literary context.
- Every accepted paragraph changes the scene in a concrete way.
- User steering reaches the next unwritten paragraph without silently rewriting accepted prose.
- A reader can open the latest chapter in both requested languages.
- No technical pipeline language appears in the fiction.

