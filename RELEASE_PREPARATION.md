# Release preparation record

Prepared 2026-11-17 from a clean source snapshot.

This is an independent, history-free community source snapshot. The original private repository, NAS production service, original data and backups were not modified.

## Scope

- General runtime, display, adapters, calendar implementation, examples, architecture documents and general tests retained.
- Original household configurations replaced by a fictional two-room offline demo; account, private host/address and hardware-specific identifiers normalized in selected code and fixtures.
- Production cutover, NAS backup/recovery, credential-handoff bundles, operational archives and their internal tool tests excluded.
- 63 assertion functions tied to the private household's configured inventory/presentation were omitted from public tests. These checked the owner's concrete devices, not a portable product contract. Generic adapter/control tests remain. This is a changed test scope, not a claim that the original entire private suite passed unchanged.
- Runtime tests adapted to the clock-only default and separate weather example; generic action wiring now supplies its own fictional device fixture. Concatenated fixture identifiers normalized consistently.
- New demo launcher, container recipes, privacy defaults and maintainer documentation added. No application feature logic or private production deployment changed.

## Validation and limits

Validation summary is recorded in VALIDATION.json. Candidate validation was local and offline. Original production integrations were not contacted or retested. No GitHub hosted CI result is claimed.

The known-identifier scan is a targeted review, not proof that arbitrary unknown secrets cannot exist. Review before publication. The maintainer subsequently verified the linux/amd64 Docker build, demo HTTP and non-root runtime on iMac; its candidate inventory hash matched. See docs/verification/docker-amd64.json. Python 3.11, ARM hardware, real household setup and legacy-iPad presentation were not revalidated in this preparation run.

## Release decisions

1. Owner selected Apache-2.0 for original project materials and Sunny Engineering attribution on 2026-11-17.
2. All 27 pinned Python distributions were reviewed and their bundled notice/license files retained. First publication is source and Docker recipes, not binary images.
3. User authorized a separate public repository under Chat202307 after third-party review and Docker verification. Proposed repository slug: SmartScreenOS-Community (original private SmartScreenOS remains unchanged). Docker verification passed on iMac.

The owner separately created Chat202307/SmartScreenOS-Community as a public repository. The original private repository visibility remains unchanged. This snapshot publishes source and recipes only, not a container image.
