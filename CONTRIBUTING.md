# Contributing

Contributions are welcome. Keep changes focused and discuss large behavioral or
protocol changes in an issue before investing substantial work.

## Development workflow

1. Fork the repository and create a topic branch from `main`.
2. Add or update tests with the implementation.
3. Run `make validate`.
4. Update user-facing documentation when behavior changes.
5. Open a pull request explaining the problem, approach, and validation.

Keep commits small and descriptive. Conventional prefixes such as `feat:`,
`fix:`, `docs:`, and `test:` are encouraged but not required.

## Pull-request checklist

- [ ] Tests cover new response shapes or behavior.
- [ ] `make validate` passes locally.
- [ ] No credentials, account identifiers, or private usage snapshots are
      included.
- [ ] GNOME resources and subprocesses are cleaned up on disable.
- [ ] Documentation and `CHANGELOG.md` are updated when appropriate.

## Reporting bugs

Use the bug-report issue form and include exact versions and reproduction
steps. Redact account data and never attach Codex credential files.

Security vulnerabilities should follow [SECURITY.md](SECURITY.md), not the
public issue tracker.
