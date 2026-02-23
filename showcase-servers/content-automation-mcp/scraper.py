import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import ipaddress
import socket


def validate_public_http_url(url: str) -> str:
    """
    Validate that the URL is HTTP/HTTPS and does not resolve to a private/internal IP.
    Raises ValueError if the URL is invalid or not allowed.
    """
    parsed = urlparse(url)

    # Require http or https and a network location
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are allowed")
    if not parsed.netloc:
        raise ValueError("URL must include a network location")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    # If an explicit port is provided, ensure it is within the valid range.
    if parsed.port is not None:
        if parsed.port <= 0 or parsed.port > 65535:
            raise ValueError("URL has an invalid port")

    try:
        # Resolve all addresses for the hostname and ensure none are private/loopback/etc.
        addrinfos = socket.getaddrinfo(hostname, None)
    except OSError as exc:
        raise ValueError(f"Unable to resolve hostname: {hostname}") from exc

    for family, _socktype, _proto, _canonname, sockaddr in addrinfos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            # Skip non-IP addresses just in case
            continue

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise ValueError("Access to private or internal network addresses is not allowed")

    return url


def fetch_html(url: str, timeout: float = 10.0) -> str:
    # First-level validation of scheme, hostname, and resolved IPs.
    safe_url = validate_public_http_url(url)

    # Re-parse and re-validate the resolved IPs immediately before making the request.
    parsed = urlparse(safe_url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except OSError as exc:
        raise ValueError(f"Unable to resolve hostname: {hostname}") from exc

    for family, _socktype, _proto, _canonname, sockaddr in addrinfos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise ValueError("Access to private or internal network addresses is not allowed")

    resp = httpx.get(safe_url, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def extract_article(url: str) -> dict:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string.strip() if soup.title else None
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n\n".join(paragraphs)

    return {"url": url, "title": title, "text": text}

def extract_links(url: str) -> list[dict]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        links.append({"text": a.get_text(" ", strip=True), "href": a["href"]})
    return links

def extract_tables(url: str) -> list[list[list[str]]]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    tables_data: list[list[list[str]]] = []
    for table in soup.find_all("table"):
        rows_data: list[list[str]] = []
        for row in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["th", "td"])]
            if cells:
                rows_data.append(cells)
        if rows_data:
            tables_data.append(rows_data)
    return tables_data
