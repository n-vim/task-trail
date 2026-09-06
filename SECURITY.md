# Security Policy

TaskTrail scans local repositories and reads project files to find TODO markers and repository gaps. Because it works with local files, safe file handling is important.

---

## Supported Versions

Security fixes are handled for the latest release and the current main branch.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| main branch | Yes |
| Older versions | No |

---

## Reporting a Vulnerability

Please do not publish security vulnerabilities in public issues.

If GitHub private vulnerability reporting is available, use it. If it is not available, open a public issue asking for a private contact method, but do not include exploit details, secret values, private repository contents, or proof-of-concept code in the public issue.

---

## Security Expectations

TaskTrail should:

- Never execute scanned project code
- Never upload repository contents anywhere
- Avoid printing secret values in reports
- Read files safely
- Respect ignored folders and generated folders
- Avoid writing outside user-selected output paths
- Keep dependencies minimal

---

## Sensitive Files

TaskTrail may detect risky repository patterns, but it should not expose sensitive values from files such as:

- `.env`
- private keys
- API token files
- cloud credentials
- local database files

If sensitive information is accidentally committed, remove it and rotate the affected secret immediately.

---

## Thank You

Responsible security reports help keep TaskTrail safe and useful for everyone.
