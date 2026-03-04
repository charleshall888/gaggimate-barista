> Source: research/multi-user-data-isolation/spec.md (bootstrapped from discovery)

# Specification: Multi-User Data Isolation — Ticket 007 Scope

## Ticket Scope

This lifecycle covers the `.gitignore` and example template work (Must Have 1 + Should Have 8):

- `.gitignore` entries for `coffees`, `grind-map.md`, `user-setup.md`, `.data-repo-path`
- `user-setup.example.md` with all sections populated with illustrative (non-personal) values
- `grind-map.example.md` with table header and one illustrative data row

## Acceptance Criteria

- `git check-ignore -v coffees` returns a match
- `git check-ignore -v grind-map.md` returns a match
- `git check-ignore -v user-setup.md` returns a match
- `git check-ignore -v .data-repo-path` returns a match
- `user-setup.example.md` committed to public repo with illustrative equipment/preferences (no real personal data)
- `grind-map.example.md` committed to public repo with header + one illustrative row
