---
name: review-ozw-pr
description: Review an incoming pull request against the siemens_ozw672 Home Assistant integration. Use when asked to review a PR on this repo, triage open PRs, or when running the PR-watch loop. Posts a review to GitHub; never merges.
---

# Reviewing a siemens_ozw672 pull request

## Authority

**Review and approve only. Never merge, never push to the PR branch, never close a PR
without the maintainer saying so.** Merging is always the maintainer's call.

Post via `gh pr review <N> --comment --body-file <file>`, or `--approve` when the PR is
clean. Use `--request-changes` only for a correctness defect you are confident about.

## Procedure

1. `gh pr view <N>` and `gh pr diff <N>`.
2. Read the **full current version** of every file the diff touches — not just the hunks.
   This repo's bugs are overwhelmingly ones where a pattern is duplicated and a fix lands
   in only one copy. You cannot see that from a diff alone.
3. Work the checklist below.
4. Post the review. Lead with what the contributor got right; they are volunteers.

## Checklist

### 1. Is the fix applied everywhere the pattern occurs?

**The single most common defect in this repo.** The same logic is copy-pasted across
`sensor.py`, `number.py`, `switch.py`, `select.py`, `binary_sensor.py`, and again across
the six sensor classes within `sensor.py`. A fix to one copy is usually incomplete.

Grep for the pattern being fixed across all five platform files before accepting.

*Precedent: PR #36 correctly fixed decimal truncation in `SiemensOzw672NumberSensor` but
left the identical bug in `SiemensOzw672EnergySensor` and `SiemensOzw672PowerSensor`.*

### 2. Does it change `unique_id` or the entity registry?

If a PR alters how `entry_id`/`unique_id` is constructed (in any platform's
`async_setup_entry`, or `entity.py`), it **orphans every existing entity for every user**
unless it ships an `async_migrate_entry` that rewrites registry entries in place.

An unmigrated `unique_id` change causes exactly the `_2`-suffix churn and history loss that
users are complaining about in issues #33/#35/#37. Flag it, hard.

*Precedent: PR #34 changed the identifier format with no migration. A user tested it and
reported it made nothing better; the author withdrew it.*

### 3. Does it change config entry `version` / `minor_version` or `.storage` shape?

Entries already on disk must keep loading. Check that `async_migrate_entry` handles the
old shape and is idempotent (safe to run twice, no-ops on already-migrated entries).

Be especially wary of type changes to `version`/`minor_version` — shipping these as strings
is what bricked users in issue #39, and the crash happens inside HA before
`async_migrate_entry` can run.

### 4. Does it swallow errors?

Reject `except: pass`, bare `except:`, and handlers that return an unbound local. The repo
already has a lot of this and we are removing it, not adding it.

A failed device write must not be reported to the user as success.

### 5. Does it fabricate data?

The OZW672 returns `'----'` for "no reading". Coercing that to `0` writes fake zeros into
long-term statistics and corrupts energy/temperature history. Missing data must surface as
unavailable, not as a number.

### 6. Correctness details worth checking by hand

- `str.isnumeric()` is `False` for `"15.8"` **and** for `"-3"`. Any guard relying on it
  mishandles decimals and negatives. Prefer `try: float(x)`.
- The `is_float()` helper in `sensor.py` returns `None` for negative decimals — it is
  broken. Do not accept new code that depends on it.
- `round(float(v), n)` vs `round(float(v, n))` — the latter is a TypeError and has been
  committed to this repo twice.
- Device classes must be real enum members. Strings like
  `"siemens_ozw672__custom_device_class"` are a legacy mechanism that modern HA rejects.

### 7. Tests

Once `tests/` exists, a behavioural change should come with a test. If the contributor
hasn't added one, say so, but don't block a correct fix on it — offer to add the test.

### 8. Quality scale direction

We are working toward Bronze. Don't accept changes that move away from it: new
`hass.data[DOMAIN]` usage instead of `entry.runtime_data`, entities without a stable
`unique_id`, or new config-flow paths that skip `_abort_if_unique_id_configured()`.

## Verdict

- **Approve** when it is correct, complete across all duplicated sites, and migration-safe.
- **Comment** when the diagnosis is right but the fix is partial — credit the diagnosis,
  name precisely what else needs doing. This is the common case.
- **Request changes** only for a definite correctness or data-loss defect.

Always state plainly what you did *not* verify — e.g. that you could not test against real
OZW672 hardware. Do not imply a level of validation you did not perform.
