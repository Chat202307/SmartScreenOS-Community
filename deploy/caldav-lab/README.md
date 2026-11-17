# Independent calendar lab — preparation only

Do not run `up`, export production files, create NAS directories or supply real
credentials without a separate explicit approval. These files are not a
production deployment and must never replace the production Compose project.

Read [the test, migration and rollback plan](../../docs/icloud-caldav-v1-independent-test-plan.md).

- `compose.yaml`: synthetic events, internal-only network/port 19081, no host
  published ports. Use Mac loopback 19080 via SSH to the approved lab IP.
- `compose.live.yaml`: explicit opt-in live overlay, CalDAV-only egress proxy and
  separate username/password secret files; no household configuration or env_file.
- `fixtures/`: entirely synthetic events and non-secret CalDAV settings.
- Do not store private files here. Use an administrator-controlled location
  outside the checkout; `private/` and `results/` are ignored as a fallback only.

Default NAS exporter invocation is a local dry-run with no SSH. Only its safe
inventory is intended for review; retain encrypted backups and identities privately.


China-region compatibility: the restricted proxy also permits only
caldav.icloud.com.cn and p[digits]-caldav.icloud.com.cn on443. The existing
public-IP validation/pinning and all other lab isolation restrictions remain.
This is a development-plan update, not authorization to run anything on NAS.
