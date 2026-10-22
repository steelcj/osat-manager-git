---
title: "Universal Cake Requirements: Add Document Slice"
dc:title: "Universal Cake Requirements: Add Document Slice"
dc:creator: "Christopher Steel"
dc:contributor: "Claude (Anthropic), AI assistance"
dc:subject: "Universal Cake, requirements, osat-manager-git, Add Document, SAT content"
dc:description: "Testable Universal Cake requirements for osat-manager-git and a git-backed Add Document interface for SAT content."
dc:date: "2026-09-30"
dc:type: "Text"
dc:format: "text/markdown"
dc:identifier: "urn:uuid:82642c55-a2c5-4800-9f24-600400f9e195"
dc:source: "en/docs/uc-requirements-add-document-slice.md, commit a02fc95"
dc:relation: "https://github.com/steelcj/uc-radar"
dc:language: "en-CA"
dc:rights: "CC-BY-4.0"
sat:version: "0.1.0"
sat:status: "Superseded"
---

# Universal Cake Requirements: Add Document Slice

> Superseded by [Decision: Build manage-git](../decisions/0001--build-manage-git-v0.1.0.md). Kept as the record of the 2026-09-30 scoping. Its baseline contract and requirement areas carry forward; its install routes through system package managers do not, because the OSAT manager contract allows no system package manager and no elevated privilege.

This is a provisional draft. The version stays provisional until Christopher Steel confirms it. It was drafted with AI assistance (Claude, Anthropic).

## Purpose and scope

This document turns the Universal Cake Evaluation Metrics <a id="cite-steel-nd-1" href="#ref-steel-nd">(Steel, n.d.)</a> into testable requirements, using one real task as the worked example: adding a document to SAT content through a friendly, git-backed interface. Every later project, including a full SAT content interface, inherits these requirements rather than starting from zero.

Two components are in scope:

- **osat-manager-git**, in full: it manages multiple git installations per machine on Linux, macOS and Windows, through the standard osat CLI with translated messages. Other osat managers depend on it.
- **The Add Document slice**: a small local web interface that writes one document into SAT content and records it in git, without the person needing to know git.

The config cascade resolver is not in scope. The slice uses one fixed content location until the cascade specification is settled.

## The worked example: Add a document

User story: as someone managing a collection, I want to add a document with a good title and description, so that it is saved safely and I can find, change or undo it later, without learning git.

1. The interface asks osat-manager-git whether the baseline is met. If not, it explains the problem in plain language and offers the fix.
2. The person fills in a form: title, description, language, and optional subject keywords. Sensible defaults are filled in where possible.
3. The tool writes a markdown file into the fixed SAT content location, with Dublin Core front matter <a id="cite-dcmi-2020-1" href="#ref-dcmi-2020">(DCMI Usage Board, 2020)</a> and a `urn:uuid:` identifier <a id="cite-davis-2024-1" href="#ref-davis-2024">(Davis et al., 2024)</a>.
4. The tool commits the file with a generated message, "Add document: {title}".
5. The person sees "Saved", and a readable history of changes, never git terms.
6. Undo is a revert, presented as "Remove this change".

## How requirements are written

Each requirement has an ID, one statement, and a test that gives a clear pass or fail. IDs use a prefix per area: ID for inclusive design, ML for multilingual, SEC for security, AL for agency and longevity, and GIT for osat-manager-git. A requirement without a test is a wish, and is moved to Open questions until it has one.

## Requirements: inclusive design

The slice meets the Web Content Accessibility Guidelines 2.2 at level AA <a id="cite-w3c-2023-1" href="#ref-w3c-2023">(World Wide Web Consortium [W3C], 2023)</a>, and every task can be completed by keyboard and screen reader alone. Automated checks use axe-core <a id="cite-deque-nd-1" href="#ref-deque-nd">(Deque Systems, n.d.)</a>.

| ID | Requirement | Test |
| --- | --- | --- |
| ID-1 | Every form field has a visible, programmatic label. | Automated check (axe) reports zero label errors. |
| ID-2 | Adding a document works by keyboard alone, in a logical focus order. | Manual run with no mouse completes the task. |
| ID-3 | Errors name the field, say what is wrong, and say how to fix it. | Screen reader (Orca, NVDA) announces each error on submit. |
| ID-4 | No git terms appear in the interface. | Interface strings contain no commit, branch, HEAD, merge or push. |
| ID-5 | Help text reads at a plain-language level. | Help text scores grade 8 or lower on a readability check. |
| ID-6 | Text and controls meet AA contrast in light and dark themes. | Automated contrast check passes in both themes. |
| ID-7 | The layout works at 400% zoom and on a phone width. | No horizontal scrolling at 320 CSS pixels wide. |

## Requirements: multilingual

The slice ships in English and French, identified by the language tags en-ca and fr-ca <a id="cite-phillips-2009-1" href="#ref-phillips-2009">(Phillips & Davis, 2009)</a>, which proves the message catalog works before more languages are added.

| ID | Requirement | Test |
| --- | --- | --- |
| ML-1 | Every interface string comes from a message catalog. | A scan finds no hard-coded strings in templates or code. |
| ML-2 | The interface is complete in en-ca and fr-ca. | Catalog check shows no missing keys in either language. |
| ML-3 | Git's own output is never shown directly; results map to catalog messages. | Forcing each known git error shows a catalog message in both languages. |
| ML-4 | The interface language and the document language are set separately. | A French-speaking person can add an English document, and the reverse. |
| ML-5 | The document's language is recorded in its metadata. | Front matter carries the chosen language tag. |
| ML-6 | Layouts survive longer French strings. | No truncated or overlapping text in fr-ca at any supported width. |

## Requirements: security

Nothing a person types can change what command runs or where a file lands. The approach follows OWASP guidance on command injection <a id="cite-owasp-ndb-1" href="#ref-owasp-ndb">(OWASP Foundation, n.d.-b)</a> and cross-site request forgery <a id="cite-owasp-nda-1" href="#ref-owasp-nda">(OWASP Foundation, n.d.-a)</a>, and git's own conventions for separating options from arguments <a id="cite-git-nda-1" href="#ref-git-nda">(Git Project, n.d.-a)</a>.

| ID | Requirement | Test |
| --- | --- | --- |
| SEC-1 | Git is called with an argument list, never through a shell. | Code review and a lint rule find no shell execution. |
| SEC-2 | User input passed to git follows `--end-of-options`. | A title starting with `--` is stored as text and runs nothing. |
| SEC-3 | File names are generated from a slug of the title, never taken raw. | Titles containing `../`, `/`, NUL or control characters write only inside the content location. |
| SEC-4 | The server listens on localhost only. | A connection from another host is refused. |
| SEC-5 | Form submissions are protected against cross-site request forgery. | A forged request from another origin is rejected. |
| SEC-6 | Git hooks <a id="cite-git-ndb-1" href="#ref-git-ndb">(Git Project, n.d.-b)</a> in the target repository do not run unless explicitly allowed. | A test hook that writes a marker file leaves no marker. |
| SEC-7 | No credentials are stored in SAT config or document metadata. | A scan of the content tree and `.assets/` finds no keys or tokens. |

## Requirements: agency and longevity

The person's content outlives the tool: it is plain files in a normal git repository they control.

| ID | Requirement | Test |
| --- | --- | --- |
| AL-1 | Documents are plain markdown with front matter. | Each file opens correctly in a plain text editor. |
| AL-2 | The repository is standard git, with no tool-specific format. | Stock git can clone, log and check out everything the tool wrote. |
| AL-3 | The person can see the full history of each document. | History view lists every change with date and author in plain words. |
| AL-4 | Every change can be undone. | "Remove this change" restores the prior state, and the removal is itself in the history. |
| AL-5 | The person can leave with everything. | An export produces the whole repository in a standard archive. |
| AL-6 | No network service is required to add, view or undo. | All tasks complete with networking disabled. |

## Requirements: osat-manager-git

osat-manager-git manages multiple git installations on each machine, on Linux, macOS and Windows, through the standard osat CLI with translated messages. Where the osat-manager specification defines the CLI, output or translation format, the specification wins over this section.

| ID | Requirement | Test |
| --- | --- | --- |
| GIT-1 | Discovers every git installation on the machine: package manager, Homebrew, Xcode, Git for Windows, portable and source builds. | On a machine with three known installations, the list command reports all three with version, path and origin. |
| GIT-2 | Installs, upgrades and removes installations through the platform's native route or a verified portable build. | Clean runs succeed on Linux Mint (apt), Fedora (dnf), macOS (Homebrew) and Windows 11 (winget). |
| GIT-3 | One installation is active per scope (machine or user); the others stay available. | Switching the active installation changes `git --version` for that scope only. |
| GIT-4 | Never removes an installation the operating system or other packages depend on without explicit confirmation. | Removing Xcode git on macOS, or a distro git with dependents, stops and asks. |
| GIT-5 | The baseline is one versioned file: minimum version, required capabilities and required config. Each installation is checked against it. | Changing the file changes what check reports, with no code change. |
| GIT-6 | Commands, options and exit codes follow the standard osat CLI, with machine-readable JSON output. | Output validates against the osat-manager schema on every platform. |
| GIT-7 | Every message comes from translation catalogs, complete in en-ca and fr-ca. | Catalog check shows no missing keys; forcing each known error shows a translated message. |
| GIT-8 | Every operation is idempotent. | A second run changes nothing and reports that. |
| GIT-9 | Packages come from signed, official sources. | Install logs show signature verification for each package. |
| GIT-10 | Required config is set at user level, never overwriting a value the person set. | An existing custom value survives, and check flags the conflict. |
| GIT-11 | Platform differences are handled: line endings, long paths and credential helper on Windows; PATH order between installations on every platform. | Check passes for the active installation on each platform, using the same baseline file. |

## Out of scope and open questions

Out of scope for this slice: the config cascade resolver, editing existing documents, remote push and pull, multi-person use, and authentication.

- [ ] Does the osat-manager specification define shared commands, output schema or exit codes that GIT-6 should adopt?
- [ ] Which minimum git version should the baseline set?
- [ ] Which Dublin Core and `sat:` fields does the Add Document form collect, beyond title, description and language?
- [ ] Are `.assets/` sidecars tracked in the same repository as content?
- [ ] Should the active installation also be settable per SAT node, through the config cascade?
- [ ] Which languages follow en-ca and fr-ca?
- [ ] Which license applies to this document?

## Changelog

| Date | Version | Change |
| --- | --- | --- |
| 2026-09-30 | 0.1.0 (provisional) | Web-ready markdown edition with APA 7 citations and References. |
| 2026-09-30 | 0.1.0 (provisional) | Revised osat-manager-git scope: multiple installations per machine, standard osat CLI, translations. |
| 2026-09-30 | 0.1.0 (provisional) | First draft, with Add Document as the worked example and osat-manager-git in full scope. |

## References

<a id="ref-davis-2024"></a>Davis, K., Peabody, B., & Leach, P. (2024). *Universally unique IDentifiers (UUIDs)* (RFC 9562). Internet Engineering Task Force. https://doi.org/10.17487/RFC9562 [Return to text](#cite-davis-2024-1)

<a id="ref-dcmi-2020"></a>DCMI Usage Board. (2020). *DCMI metadata terms*. Dublin Core Metadata Initiative. https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ [Return to text](#cite-dcmi-2020-1)

<a id="ref-deque-nd"></a>Deque Systems. (n.d.). *axe-core* [Computer software]. GitHub. https://github.com/dequelabs/axe-core [Return to text](#cite-deque-nd-1)

<a id="ref-git-nda"></a>Git Project. (n.d.-a). *gitcli: Git command-line interface and conventions*. Git documentation. https://git-scm.com/docs/gitcli [Return to text](#cite-git-nda-1)

<a id="ref-git-ndb"></a>Git Project. (n.d.-b). *githooks: Hooks used by Git*. Git documentation. https://git-scm.com/docs/githooks [Return to text](#cite-git-ndb-1)

<a id="ref-owasp-nda"></a>OWASP Foundation. (n.d.-a). *Cross-site request forgery prevention cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html [Return to text](#cite-owasp-nda-1)

<a id="ref-owasp-ndb"></a>OWASP Foundation. (n.d.-b). *OS command injection defense cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html [Return to text](#cite-owasp-ndb-1)

<a id="ref-phillips-2009"></a>Phillips, A., & Davis, M. (2009). *Tags for identifying languages* (BCP 47, RFC 5646). Internet Engineering Task Force. https://doi.org/10.17487/RFC5646 [Return to text](#cite-phillips-2009-1)

<a id="ref-steel-nd"></a>Steel, C. (n.d.). *Universal Cake evaluation metrics* [Unpublished manuscript, uc-radar repository]. GitHub. https://github.com/steelcj/uc-radar [Return to text](#cite-steel-nd-1)

<a id="ref-w3c-2023"></a>World Wide Web Consortium. (2023). *Web content accessibility guidelines (WCAG) 2.2* (W3C Recommendation). https://www.w3.org/TR/WCAG22/ [Return to text](#cite-w3c-2023-1)
