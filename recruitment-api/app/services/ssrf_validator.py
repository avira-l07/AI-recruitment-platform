"""URL safety validation does not establish link accessibility.

Future fetchers must revalidate redirects and pin the validated destination IP.
"""
import ipaddress
import socket
import urllib.parse
from typing import Tuple


def _public_address(value):
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast


def is_safe_url(url_string: str) -> Tuple[bool, str]:
    if not isinstance(url_string, str) or not url_string.strip():
        return False, "Empty or invalid URL string"
    url = url_string.strip()
    if any(c.isspace() or ord(c) < 32 for c in url) or "\\" in url:
        return False, "Invalid characters in URL"
    if "://" not in url:
        url = "https://" + url
    try:
        parsed = urllib.parse.urlsplit(url)
        host, port = parsed.hostname, parsed.port
        if parsed.scheme.lower() not in {"http", "https"}:
            return False, "Only HTTP and HTTPS URLs are supported"
        if not host or parsed.username is not None or parsed.password is not None:
            return False, "Missing host or prohibited URL credentials"
        host = host.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return False, "Prohibited local hostname"
        if port is not None and port not in {80, 443, 8080, 8443}:
            return False, "Non-standard port prohibited"
        try:
            ipaddress.ip_address(host)
            addresses = [host]
        except ValueError:
            addresses = [item[4][0] for item in socket.getaddrinfo(host, port or 443, type=socket.SOCK_STREAM)]
        if not addresses or not all(_public_address(value) for value in addresses):
            return False, "Target includes a non-public IP address"
    except (ValueError, OSError, UnicodeError):
        return False, "Invalid URL or hostname could not be resolved"
    return True, url
