"""Apple-only, read-only transport guards; no telemetry, logging or file writes."""
from datetime import datetime, timezone
import re
from urllib.parse import urlsplit, urljoin
from xml.etree import ElementTree as ET

import caldav
from caldav.lib.url import URL
from icalendar import Calendar


ALLOWED_METHODS = frozenset(('GET', 'HEAD', 'OPTIONS', 'PROPFIND', 'REPORT'))


class Refused(RuntimeError):
    def __init__(self, reason=0, family=0):
        super().__init__('local read-only policy refused request')
        self.reason = reason
        self.family = family


def target_family(host):
    # Fixed numeric categories; never retain or report a host or URL.
    if re.fullmatch(r'(?:p[0-9]+-)?caldav\.icloud\.com', host):
        return 1
    if re.fullmatch(r'(?:p[0-9]+-)?caldav\.icloud\.com\.cn', host):
        return 2
    if host.endswith('.icloud.com') or host.endswith('.icloud.com.cn'):
        return 3
    return 4


def validate_target(url):
    try:
        target = urlsplit(str(url))
        family = target_family(target.hostname or '')
        port = target.port
    except ValueError:
        raise Refused(10) from None
    if target.scheme != 'https':
        raise Refused(1, family)
    if target.username is not None or target.password is not None:
        raise Refused(2, family)
    if port not in (None, 443):
        raise Refused(3, family)
    if target.fragment:
        raise Refused(4, family)
    if family not in (1, 2):
        raise Refused(5, family)


def validate_request(method, url, body=None):
    validate_target(url)
    if method not in ALLOWED_METHODS:
        raise Refused(6)
    if method == 'REPORT':
        if not isinstance(body, (str, bytes)) or b'<!DOCTYPE' in (body.encode() if isinstance(body, str) else body).upper():
            raise Refused(7)
        try:
            root = ET.fromstring(body)
        except Exception:
            raise Refused(7) from None
        if root.tag != '{urn:ietf:params:xml:ns:caldav}calendar-query':
            raise Refused(8)


class Guard:
    def __init__(self):
        self.policy_reason = 0
        self.target_family_code = 0
        self.error_code = 0
        self.last_http_status = 0
        self.last_target_family_code = 0
        self.last_request_kind = 0
        self.last_request_timeout_seconds = 0
        self.successful_reports = 0
        self.requests = 0
        self.reports = 0
        self.calendars = 0
        self.blocked = 0
        self.fail = False
        self.slow = False
        self.coverage = {key: 0 for key in ('recurring_resources', 'exception_components',
                         'exdate_components', 'rdate_components', 'cancelled_components', 'all_day_components', 'timezone_components',
                         'utc_components', 'floating_components')}

    def record_refusal(self, error):
        self.error_code = 7
        self.policy_reason = error.reason
        self.target_family_code = error.family

    def check(self, method, url, body=None):
        try:
            validate_request(method, url, body)
        except Refused as error:
            self.record_refusal(error)
            raise

    def before(self, method, url, body=None):
        self.check(method, url, body)
        if self.fail:
            self.blocked += 1
            raise OSError('local process-only network failure')
        if self.slow:
            # Delay only inside this test process, before contacting Apple.
            import time
            time.sleep(1)
            raise TimeoutError('local process-only deadline test')
        self.requests += 1
        self.reports += method == 'REPORT'

    def observe(self, response):
        tree = response.tree
        if tree is None:
            return
        for node in tree.findall('.//{urn:ietf:params:xml:ns:caldav}calendar-data'):
            if len((node.text or '').encode('utf-8')) > 2 * 1024 * 1024:
                raise Refused(9)
            data = Calendar.from_ical(node.text or '')
            for event in data.walk('VEVENT'):
                for key, prop in (('recurring_resources', 'RRULE'), ('exception_components', 'RECURRENCE-ID'),
                                  ('exdate_components', 'EXDATE'), ('rdate_components', 'RDATE')):
                    self.coverage[key] += prop in event
                self.coverage['cancelled_components'] += str(event.get('STATUS', '')).upper() == 'CANCELLED'
                start = event.get('DTSTART')
                if start is None:
                    continue
                value = start.dt
                if not isinstance(value, datetime):
                    key = 'all_day_components'
                elif start.params.get('TZID'):
                    key = 'timezone_components'
                elif value.tzinfo is None:
                    key = 'floating_components'
                else:
                    key = 'utc_components'
                self.coverage[key] += 1


def make_client(guard, *, use_lab_proxy=False, **options):
    validate_target(options['url'])
    if options.get('ssl_verify_cert') is not True:
        raise Refused(11)

    class ReadOnlyClient(caldav.DAVClient):
        def _follows_redirects(self, method):
            return False  # Never let the HTTP library follow unchecked redirects.

        def _redirect_target(self, method, url_obj, status_code, headers):
            if status_code not in (301, 302, 307, 308) or not headers.get('Location'):
                return None
            target = urljoin(str(url_obj), headers['Location'])
            try:
                validate_target(target)
            except Refused as error:
                guard.record_refusal(error)
                raise
            return URL.objectify(target)

        def principal(self, *args, **kwargs):
            principal = super().principal(*args, **kwargs)
            original = principal.calendars
            def calendars(*args, **kwargs):
                result = original(*args, **kwargs)
                guard.calendars = len(result)
                return result
            principal.calendars = calendars
            return principal

        def report(self, *args, **kwargs):
            response = super().report(*args, **kwargs)
            guard.observe(response)
            return response

    if use_lab_proxy:
        options['proxy'] = 'http://egress-proxy:3128'
    client = ReadOnlyClient(**options)
    client.MAX_REDIRECTS = 5
    client.session.trust_env = False
    client.session.proxies.clear()
    original_request = client.session.request
    original_send = client.session.send

    def request(method, url, **kwargs):
        try:
            guard.before(method, str(url), kwargs.get('data'))
        except Refused as error:
            guard.record_refusal(error)
            raise
        guard.last_target_family_code = target_family(urlsplit(str(url)).hostname or '')
        guard.last_request_kind = {'PROPFIND': 1, 'REPORT': 2, 'GET': 3, 'HEAD': 4, 'OPTIONS': 5}.get(method, 0)
        timeout = kwargs.get('timeout')
        guard.last_request_timeout_seconds = float(timeout) if type(timeout) in (int, float) else 0
        kwargs['allow_redirects'] = False
        kwargs['proxies'] = {'https': 'http://egress-proxy:3128'} if use_lab_proxy else {}
        # Never inherit a household, iMac or VPN proxy configuration.
        try:
            response = original_request(method, url, **kwargs)
        except Refused as error:
            guard.record_refusal(error)
            raise
        except Exception as error:
            # Classify without reading/printing exception messages, URLs or bodies.
            name = type(error).__name__.lower()
            guard.error_code = (3 if 'ssl' in name or 'certificate' in name else
                                2 if 'timeout' in name else
                                4 if isinstance(error, OSError) or 'connection' in name else 9)
            raise
        guard.last_http_status = int(response.status_code)
        if method == 'REPORT' and response.status_code == 207:
            guard.successful_reports += 1
        if response.status_code in (401, 403):
            guard.error_code = 1
        elif response.status_code == 429:
            guard.error_code = 5
        elif response.status_code >= 500:
            guard.error_code = 6
        return response

    def send(prepared, **kwargs):
        # A second gate immediately before the actual HTTP transport.
        guard.check(prepared.method, prepared.url, prepared.body)
        kwargs['allow_redirects'] = False
        return original_send(prepared, **kwargs)

    client.session.request = request
    client.session.send = send
    return client
