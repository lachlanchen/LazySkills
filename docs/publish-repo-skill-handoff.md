# Publish Repo Skill Handoff

Date: 2026-06-06

## Summary

The `publish-repo` skill was synced from the GaugeHand project into LazySkills so Codex, AgInTiFlow, Claude, Gemini, GitHub Copilot, and generic local-tool agents can reuse the same GitHub publication workflow.

Canonical LazySkills location:

```text
$LAZYSKILLS_ROOT/skills/publish-repo/
```

Original GaugeHand source location:

```text
$GAUGEHAND_ROOT/skills/publish-repo/
```

## What The Skill Does

`publish-repo` publishes a local git repository to GitHub after the agent has prepared public-facing repo content and committed local changes.

It covers:

- repository readiness checks;
- README/resource review;
- clean worktree enforcement;
- GitHub CLI authentication checks;
- GitHub repo creation when missing;
- `origin` setup;
- current-branch push with upstream tracking;
- GitHub description, homepage, and topic metadata;
- final metadata verification.

The bundled helper is:

```text
skills/publish-repo/scripts/publish_repo.sh
```

It intentionally refuses dirty worktrees. The agent must commit or stop before publishing.

## Codex Usage

For repo-local use, from the repository root:

```bash
skills/publish-repo/scripts/publish_repo.sh \
  --owner lachlanchen \
  --repo ExampleRepo \
  --visibility public \
  --homepage https://lazying.art \
  --description "Short repository description" \
  --topics "topic-one,topic-two,lazying-art"
```

For LazySkills-installed use, keep the working directory at the target repository root but call the helper by absolute path:

```bash
$LAZYSKILLS_ROOT/skills/publish-repo/scripts/publish_repo.sh \
  --owner lachlanchen \
  --repo ExampleRepo \
  --visibility public \
  --homepage https://lazying.art \
  --description "Short repository description" \
  --topics "topic-one,topic-two,lazying-art"
```

Install into Codex:

```bash
cd $LAZYSKILLS_ROOT
python3 scripts/lazyskills.py install --platform codex publish-repo
```

## AgInTi Usage

Preferred external pack mode:

```bash
export AGINTIFLOW_SKILL_PACKS=$LAZYSKILLS_ROOT
aginti skills "publish repo"
```

Project-local copy mode:

```bash
cd /path/to/project
python3 $LAZYSKILLS_ROOT/scripts/lazyskills.py install \
  --platform aginti \
  --scope project \
  publish-repo
```

The skill also includes an AgInTi-compatible task contract:

```text
skills/publish-repo/references/aginti-compatibility.md
```

## Validation

Run from LazySkills root:

```bash
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py list --json
bash -n skills/publish-repo/scripts/publish_repo.sh
```

Optional smoke test without publishing:

```bash
skills/publish-repo/scripts/publish_repo.sh --help
```

Do not run the full publish command against a real repo unless:

- `gh auth status` succeeds;
- the target repo name and owner are correct;
- the target worktree is clean;
- the user asked to publish.

## Files Added To LazySkills

```text
skills/publish-repo/SKILL.md
skills/publish-repo/agents/openai.yaml
skills/publish-repo/references/aginti-compatibility.md
skills/publish-repo/scripts/publish_repo.sh
docs/publish-repo-skill-handoff.md
```

Catalog and docs updates:

```text
skills.json
README.md
website/index.html
```

## Maintenance Notes

- Keep `skills.json` synchronized when the skill is renamed, moved, or removed.
- Keep `SKILL.md` concise; put deeper platform or agent contract details in `references/`.
- Do not add secrets, GitHub tokens, cookies, or user-specific auth data.
- Keep the helper script argument-driven and shellcheck-friendly.
- If GitHub CLI changes `gh repo create` or `gh repo edit` flags, update the script and rerun validation.

## Completion Criteria For Future Syncs

A future sync is complete when:

- GaugeHand and LazySkills skill bodies intentionally match or the divergence is documented.
- `python3 scripts/lazyskills.py validate` passes in LazySkills.
- `bash -n skills/publish-repo/scripts/publish_repo.sh` passes.
- `skills.json` includes `publish-repo`.
- README and website skill count are updated.
- LazySkills changes are committed and pushed.
