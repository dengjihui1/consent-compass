# Release checklist

- [x] `SKILL.md` has valid frontmatter and a discriminating description.
- [x] Core engine does not require a model, API key, network, or raw records.
- [x] Explicit prohibitions override permissions.
- [x] Missing evidence is not interpreted as permission.
- [x] Every finding includes a rule ID and evidence list.
- [x] Public demos contain synthetic metadata only.
- [x] JSON, Markdown, and HTML reports are generated locally.
- [x] Tests cover blocked, allowed, unknown, and deterministic behavior.
- [x] CI covers Python 3.9, 3.11, and 3.13.
- [x] Run the package validator immediately before packaging.
- [x] Build exactly one final zip inside this project folder.
- [x] Verify the zip excludes `.git`, generated output, caches, and raw data.
