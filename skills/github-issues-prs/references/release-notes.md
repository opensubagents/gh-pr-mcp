# Release notes / changelog from merged PRs

The job: turn a list of merged PRs (or a compare URL) into release notes that a human reading the project's changelog will actually find useful.

## Inputs

The user might give you any of these:

- **A compare URL** like `https://github.com/{owner}/{repo}/compare/v1.2.0...v1.3.0` — fetch with `.diff` appended for the raw diff, or visit the page for the list of commits/PRs.
- **A list of PR URLs or numbers.** Fetch each.
- **A milestone or label** (e.g., "all PRs labeled `release/2.4`"). Without an MCP connector you can't list these directly — ask the user to paste the list.
- **Pasted PR titles and descriptions.**

If all you have is a list of commit SHAs, those are usually less useful than the PRs that produced them — ask whether the user can give you the PR list instead.

## Audience

Release notes have two audiences and you have to serve both:

1. **End users** — what changed in a way that affects them? New features, bug fixes they'll feel, breaking changes they need to act on.
2. **Operators / integrators** — config changes, deprecations, migration steps, dependency updates.

Internal refactors that don't affect either audience usually don't belong in user-facing release notes (though they might belong in an internal changelog).

## Default structure

Follow [Keep a Changelog](https://keepachangelog.com)-style sections unless the project has its own conventions:

```markdown
## {version} — {date}

### ⚠️ Breaking changes
- ... (#PR)

### Added
- ... (#PR)

### Changed
- ... (#PR)

### Fixed
- ... (#PR)

### Deprecated
- ... (#PR)

### Removed
- ... (#PR)

### Security
- ... (#PR)
```

Omit empty sections. Put **Breaking** first — readers scan for that. **Security** is also worth surfacing prominently if there are security fixes.

## Writing the entries

Each entry is one line. Make it:

- **User-visible.** "Refactored auth module" → "Login is now ~40% faster on cold start." If you can't translate it into something user-visible, it probably doesn't belong here.
- **Concrete.** "Improved performance" tells the reader nothing. Numbers, scenarios, or named features are better.
- **Past tense, active voice.** "Added X." "Fixed Y when Z."
- **Linked.** Put the PR number in parens at the end: `(#1234)`. If you have the URL, it'll auto-link on GitHub.
- **Credited where appropriate.** For external contributors, append `(thanks @username!)`. Don't credit maintainers for routine work — it gets noisy.

## Breaking changes deserve more than one line

For each breaking change, include a short migration block:

```markdown
### ⚠️ Breaking changes

- **`config.timeout` no longer accepts strings** (#1234)
  Pass a number of milliseconds instead. To migrate:
  ```diff
  - timeout: "30s"
  + timeout: 30_000
  ```
```

Even a sentence of "to migrate, do X" saves your users a lot of time.

## When to consult the diff vs. the description

PR descriptions are the easy source — they tell you what the author thought they were doing. But authors miss things, and the description sometimes diverges from the merged code (especially after review changes).

For a typical release notes pass, the descriptions are enough. For a major release where accuracy matters more, spot-check by fetching the diffs of the largest PRs.

## Output

Markdown artifact, ready to paste into `CHANGELOG.md` or a GitHub Release body.

If the project uses a different format (Conventional Commits-generated, custom template, RST), match it. Look at the previous release entry for cues.
