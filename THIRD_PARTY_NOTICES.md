# Third-party notices and source distribution review

SmartScreenOS original code is Copyright 2026 Sunny Engineering, Apache-2.0. Dependencies are separate works under the terms below, not relicensed Apache-2.0. This source candidate does not vendor dependency implementation code or binary wheels. Exact installed distribution versions were matched against all 27 requirements.lock entries; bundled license/notice texts are preserved without altering upstream author names or public attribution addresses.

Dual-license selections: use Apache-2.0 for caldav, calendaring-config, icalendar-searcher and packaging where offered; use the BSD-3-Clause/EDL option for paho-mqtt. python-dateutil has contribution-specific Apache and BSD terms, so preserve its complete notice. qh3's metadata omitted a license expression; its included text was inspected as BSD-3-Clause. lxml's LICENSES.txt records additional included component terms and must be retained; do not treat its entire wheel as only BSD.

recurring-ical-events and x-wr-timezone are LGPL-3.0-or-later. SmartScreenOS uses them through separate unmodified Python modules; no code was copied from these libraries into the application. Preserve their notices and GPL/LGPL texts. Users may inspect, modify and replace these modules. For a distributed container, provide the exact corresponding library sources alongside it and retain replacement/rebuild instructions; a link to a general project homepage alone is not the source-delivery plan. No built image is distributed in this release preparation.

The intended first public release is source + Docker recipes only. Before distributing images, separately collect the actual image's dependency/base-OS notices and corresponding sources, including bundled native subcomponents. This source review does not certify an as-yet-unbuilt image. Docker verification does not publish an image.

| Dependency | Exact version | Declared or inspected license | Notices |
|---|---|---|---|
| caldav | 3.7.0 | GPL-3.0-or-later OR Apache-2.0 | [license files](third_party/licenses/caldav/) |
| calendaring-config | 0.5.0 | GPL-3.0-or-later OR Apache-2.0 | [license files](third_party/licenses/calendaring-config/) |
| charset-normalizer | 3.5.2 | MIT | [license files](third_party/licenses/charset-normalizer/) |
| click | 8.5.1 | BSD-3-Clause | [license files](third_party/licenses/click/) |
| dnspython | 2.9.2 | ISC | [license files](third_party/licenses/dnspython/) |
| h11 | 0.16.0 | MIT | [license files](third_party/licenses/h11/) |
| icalendar | 7.3.0 | BSD-2-Clause | [license files](third_party/licenses/icalendar/) |
| icalendar-searcher | 1.3.0 | GPL-3.0-or-later OR Apache-2.0 | [license files](third_party/licenses/icalendar-searcher/) |
| iniconfig | 2.3.1 | MIT | [license files](third_party/licenses/iniconfig/) |
| jh2 | 5.0.15 | MIT | [license files](third_party/licenses/jh2/) |
| lxml | 6.1.3 | BSD-3-Clause | [license files](third_party/licenses/lxml/) |
| niquests | 3.21.3 | Apache-2.0 | [license files](third_party/licenses/niquests/) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | [license files](third_party/licenses/packaging/) |
| paho-mqtt | 2.2.0 | EPL-2.0 OR BSD-3-Clause | [license files](third_party/licenses/paho-mqtt/) |
| pluggy | 1.7.0 | MIT | [license files](third_party/licenses/pluggy/) |
| pygments | 2.21.0 | BSD-2-Clause | [license files](third_party/licenses/pygments/) |
| pytest | 9.2.0 | MIT | [license files](third_party/licenses/pytest/) |
| python-dateutil | 2.9.0.post0 | Apache-2.0 AND BSD-3-Clause (per-contribution terms) | [license files](third_party/licenses/python-dateutil/) |
| pyyaml | 6.0.3 | MIT | [license files](third_party/licenses/pyyaml/) |
| qh3 | 2.1.0 | BSD-3-Clause (LICENSE text inspected) | [license files](third_party/licenses/qh3/) |
| recurring-ical-events | 3.8.2 | LGPL-3.0-or-later | [license files](third_party/licenses/recurring-ical-events/) |
| six | 1.17.0 | MIT | [license files](third_party/licenses/six/) |
| tzdata | 2026.6 | Apache-2.0 | [license files](third_party/licenses/tzdata/) |
| urllib3-future | 2.25.906 | MIT | [license files](third_party/licenses/urllib3-future/) |
| wassima | 2.1.5 | MIT | [license files](third_party/licenses/wassima/) |
| websockets | 16.1.1 | BSD-3-Clause | [license files](third_party/licenses/websockets/) |
| x-wr-timezone | 2.0.1 | LGPL-3.0-or-later | [license files](third_party/licenses/x-wr-timezone/) |

Machine-readable provenance and license-file hashes: third_party/dependencies.json.

Primary references: https://www.apache.org/licenses/LICENSE-2.0 and https://www.gnu.org/licenses/lgpl-3.0.html .
