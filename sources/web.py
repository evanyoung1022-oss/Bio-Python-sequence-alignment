"""The one place where the app downloads things from the internet.

Every database call goes through fetch(), so they all share the same timeout, identify
the app the same way, and turn network problems into a SourceError with a message that
is safe to show on the page. Tests replace fetch() with a fake so they run offline."""
import gzip
import json
import urllib.error
import urllib.request

# Some databases (AlphaFold) refuse requests that don't say what program is asking
USER_AGENT = "protein-explorer/2.0 (github.com/evanyoung1022-oss/Bio-Python-sequence-alignment)"


class SourceError(Exception):
    """A database was slow, unreachable or answered with an error."""


class NotFound(SourceError):
    """The database answered, but has no record with that ID (HTTP 404)."""


def fetch(url, payload=None, timeout=30, source="the database"):
    """Download a URL and return its text. With `payload`, POST it as JSON.
    Files ending in .gz are unzipped. An empty answer comes back as ""."""
    headers = {"User-Agent": USER_AGENT}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise NotFound(source + " has no record for that ID.") from error
        raise SourceError(source + " answered with an error (HTTP " + str(error.code) + "). "
                          "It may be busy, so try again in a minute.") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise SourceError(source + " didn't answer in time. It may be slow right now, "
                          "or your internet connection dropped. Try again in a minute.") from error
    if url.endswith(".gz"):
        body = gzip.decompress(body)
    return body.decode("utf-8", errors="replace")


def fetch_json(url, payload=None, timeout=30, source="the database"):
    """fetch() for JSON answers. An empty answer (some searches return nothing at all
    when there are no hits) comes back as an empty dict."""
    text = fetch(url, payload, timeout, source)
    return json.loads(text) if text.strip() else {}
