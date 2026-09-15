# Security Policy

## Supported Versions

Security fixes apply to the current development branch and the latest published
release.

| Version | Supported |
| --- | --- |
| Current `master` | Yes |
| Latest release | Yes |
| Older releases | Best effort |

## Reporting a Vulnerability

Please do not report security issues in a public GitHub issue.

Report them privately through GitHub's private security reporting or by
contacting the project maintainers privately. Include:

- A clear description of the issue
- Steps to reproduce it
- Affected files, commands, or versions
- Potential impact
- Any suggested mitigation

Please allow maintainers reasonable time to investigate before publicly
disclosing the issue.

## Relevant Scope

Security reports may include:

- Unsafe save or load behavior
- Arbitrary file access or path traversal
- Unsafe content scaffolding or validation
- Dependency vulnerabilities
- Accidental secrets or credentials
- Code execution caused by crafted project data
- Reproducible corruption of persistent game state

Dungeon Drifters currently has no network service, account system, cloud save
system, or multiplayer backend. Issues involving those systems are outside the
current release scope unless they affect repository tooling or future-facing
code.

## Response

Maintainers will acknowledge credible reports, investigate the issue, and
determine whether a fix or mitigation is needed. Valid reports may result in a
patch, documentation update, or release notice.

## Safe Harbor

Good-faith security research is welcome when it:

- Avoids accessing or altering other people's data
- Avoids service disruption
- Does not use social engineering or physical attacks
- Reports the issue privately and responsibly
