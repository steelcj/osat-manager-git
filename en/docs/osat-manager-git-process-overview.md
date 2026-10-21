---
title: "Creating the Initial osat-manager-git: Process Overview"
description: "How the initial osat-manager-git was scoped and planned: from feasibility to a unified git base, Universal Cake requirements, and a proposed build sequence."
identifier: "urn:uuid:90391798-a7d9-4f30-b7c1-bd9e40bba160"
language: "en-ca"
creator: "Christopher Steel"
date: "2026-09-30"
version: "0.1.0"
status: "provisional"
relation: "https://github.com/steelcj/uc-radar"
---

# Creating the Initial osat-manager-git: Process Overview

osat-manager-git is being built first as a unified git base: it manages multiple git installations on Linux, macOS and Windows through the standard osat CLI, with translated messages, so that every other osat manager can rely on git being present and correct. This overview records how that decision was reached and how the work proceeds. It is a provisional draft, drafted with AI assistance (Claude, Anthropic), and stays provisional until Christopher Steel confirms it.

## Where this fits

The long-term goal is highly accessible, safe, secure and multilingual applications, measured against the Universal Cake Evaluation Metrics <a id="cite-steel-nd-1" href="#ref-steel-nd">(Steel, n.d.)</a>. One example is a very user-friendly, git-backed interface for managing SAT content, where a person adds a document, gives it a good title and description, and never needs to learn git.

That interface depends on git working the same way everywhere. osat-manager-git provides that foundation, and building it is also the first chance to turn the Universal Cake metrics into concrete, testable requirements.

## Step one: confirm feasibility

Two meanings of "managing git" were considered: managing git itself, and managing repositories inside a SAT hierarchy. Both are feasible. Managing git itself came first, because the repository work depends on it and because the SAT config cascade specification is still being written.

## Step two: define a baseline contract, not an install method

The central idea is a baseline contract that says what "git is ready" means:

- a minimum git version;
- the capabilities other osat managers rely on;
- required configuration, such as line endings, `safe.directory`, credential helper, and long paths on Windows.

Other managers ask osat-manager-git whether the contract is met, rather than probing git themselves. How git gets installed matters less than whether the contract holds.

## Step three: set the scope

The first plan was a thin check-only stub. That changed: the full manager is needed in the short term, because other osat managers need git soon. The agreed scope is:

- manage multiple git installations per machine, not just one;
- run on Linux, macOS and Windows;
- follow the standard osat CLI defined by the osat-manager specification;
- provide translated messages, starting with en-ca and fr-ca.

Where the osat-manager specification defines commands, output or translation format, the specification takes precedence over this project's own documents.

## Step four: write Universal Cake requirements through a worked example

General metrics become useful only when a real task forces them into testable statements. The chosen task is "Add a document" to SAT content, done end to end:

1. The interface asks osat-manager-git whether the baseline is met, and explains any problem in plain language.
2. The person fills in title, description and language.
3. The tool writes a markdown file with Dublin Core front matter and a `urn:uuid:` identifier.
4. The tool records the change in git with a generated message.
5. The person sees "Saved" and a readable history, and can undo with "Remove this change".

Each requirement gets an ID, one statement, and a test with a clear pass or fail. They fall into five areas.

| Area | Prefix | What it secures |
| --- | --- | --- |
| Inclusive design | ID | WCAG 2.2 level AA <a id="cite-w3c-2023-1" href="#ref-w3c-2023">(World Wide Web Consortium [W3C], 2023)</a>, keyboard and screen-reader use, plain language, no git terms. |
| Multilingual | ML | All strings from a message catalog; en-ca and fr-ca language tags <a id="cite-phillips-2009-1" href="#ref-phillips-2009">(Phillips & Davis, 2009)</a>; git's own output never shown directly. |
| Security | SEC | No shell, `--end-of-options` before user input <a id="cite-git-nd-1" href="#ref-git-nd">(Git Project, n.d.)</a>, safe file names, localhost only, hooks off by default <a id="cite-owasp-nd-1" href="#ref-owasp-nd">(OWASP Foundation, n.d.)</a>. |
| Agency and longevity | AL | Plain markdown in standard git, full history, undo, export, no network dependency. |
| osat-manager-git | GIT | Discovery, install and removal, active installation per scope, baseline checks, osat CLI conformance, translations, idempotence, signed sources. |

These requirements are recorded in the companion document, *Universal Cake Requirements: Add Document Slice*.

## Design principles carried forward

These principles came out of the feasibility work and guide later projects, including the web interface.

- **The git CLI is the engine.** Parsing git's machine-readable porcelain output gives access to all of git. Libraries such as libgit2 or isomorphic-git are used only where they clearly help, because they do not cover all of git.
- **Progressive disclosure.** Common tasks get excellent guided flows; advanced operations stay reachable but out of the way.
- **Security from day one.** A service that runs git is attack surface: each repository is sandboxed, and hooks from untrusted repositories are treated as code execution.
- **Translate meaning, not git.** Structured results map to the project's own message catalog, so every language gets the same clarity.
- **Hardest accessibility first.** Diffs and merge conflicts are the hardest things to make screen-reader friendly, so they are prototyped early.

## Proposed build sequence

This order is proposed, not yet confirmed.

1. Write the baseline contract as one versioned file.
2. Build discovery: list every git installation with version, path and origin.
3. Build check: report each installation against the baseline as JSON, following the osat CLI.
4. Build install, upgrade and remove through each platform's native route: apt, dnf, Homebrew and winget.
5. Build active-installation switching per machine and per user.
6. Complete the en-ca and fr-ca catalogs, and test on Linux Mint, Fedora, macOS and Windows 11.
7. Build the Add Document slice on top, and test it against the Universal Cake requirements.

## Before building an interface: evaluate prior art

GitHub Desktop, GitButler and Forgejo should be evaluated against the Universal Cake metrics first. The results show which gaps in accessibility, language support and safety a new interface would actually fill.

## Open questions

- Which shared commands, output schema and exit codes does the osat-manager specification define?
- Which minimum git version does the baseline set?
- Can the active installation also be set per SAT node, through the config cascade?
- Which Dublin Core and `sat:` fields does the Add Document form collect?
- Which languages follow en-ca and fr-ca?
- Which license applies to this document?

## Changelog

| Date | Version | Change |
| --- | --- | --- |
| 2026-09-30 | 0.1.0 (provisional) | First draft of the process overview. |

## References

<a id="ref-git-nd"></a>Git Project. (n.d.). *gitcli: Git command-line interface and conventions*. Git documentation. https://git-scm.com/docs/gitcli [Return to text](#cite-git-nd-1)

<a id="ref-owasp-nd"></a>OWASP Foundation. (n.d.). *OS command injection defense cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html [Return to text](#cite-owasp-nd-1)

<a id="ref-phillips-2009"></a>Phillips, A., & Davis, M. (2009). *Tags for identifying languages* (BCP 47, RFC 5646). Internet Engineering Task Force. https://doi.org/10.17487/RFC5646 [Return to text](#cite-phillips-2009-1)

<a id="ref-steel-nd"></a>Steel, C. (n.d.). *Universal Cake evaluation metrics* [Unpublished manuscript, uc-radar repository]. GitHub. https://github.com/steelcj/uc-radar [Return to text](#cite-steel-nd-1)

<a id="ref-w3c-2023"></a>World Wide Web Consortium. (2023). *Web content accessibility guidelines (WCAG) 2.2* (W3C Recommendation). https://www.w3.org/TR/WCAG22/ [Return to text](#cite-w3c-2023-1)
