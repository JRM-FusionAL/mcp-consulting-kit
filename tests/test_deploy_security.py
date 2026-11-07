"""Offline checks that the public proxy fails closed and examples stay on loopback.

Run from the repo root: python3 -m unittest tests.test_deploy_security -v
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


class ProxyAuthTests(unittest.TestCase):
    def test_mcp_conf_requires_basic_auth_at_server_scope(self):
        conf = read("deploy/nginx/mcp.conf")
        server_part, _, _ = conf.partition("location ")
        self.assertIn('auth_basic "FusionAL MCP";', server_part)
        self.assertIn("auth_basic_user_file /etc/nginx/.htpasswd;", server_part)

    def test_only_healthz_is_exempt_from_basic_auth(self):
        conf = read("deploy/nginx/mcp.conf")
        blocks = re.findall(r"location[^{]*\{[^}]*\}", conf)
        exempt = [b for b in blocks if "auth_basic off;" in b]
        self.assertEqual(len(exempt), 1)
        self.assertIn("location = /healthz", exempt[0])

    def test_nginx_conf_requires_basic_auth(self):
        conf = read("nginx.conf")
        self.assertIn('auth_basic "FusionAL MCP";', conf)
        self.assertIn("auth_basic_user_file /etc/nginx/.htpasswd;", conf)
        # auth must come before the first location so it covers every route
        self.assertLess(conf.index("auth_basic "), conf.index("location "))


class ComposeMountTests(unittest.TestCase):
    def _htpasswd_mount_is_fail_closed(self, rel: str):
        text = read(rel)
        self.assertIn("source: ./deploy/nginx/.htpasswd", text, rel)
        self.assertIn("target: /etc/nginx/.htpasswd", text, rel)
        self.assertIn("create_host_path: false", text, rel)
        # the old short-syntax mount is what let Docker create an empty directory
        self.assertNotIn(":/etc/nginx/.htpasswd", text, rel)

    def test_proxy_compose_refuses_missing_htpasswd(self):
        self._htpasswd_mount_is_fail_closed("docker-compose.proxy.yaml")

    def test_nginx_compose_refuses_missing_htpasswd(self):
        self._htpasswd_mount_is_fail_closed("nginx-compose.yaml")


class LoopbackPortTests(unittest.TestCase):
    def _published_ports(self, rel: str):
        text = read(rel)
        return re.findall(r'^\s*-\s*"([^"]*:\d+)"\s*$', text, re.MULTILINE)

    def test_example_ports_bind_loopback(self):
        cases = {
            "docker-compose.fusional.yaml": ["127.0.0.1:8009:8009"],
            "docker-compose.next-server.example.yaml": ["127.0.0.1:8105:8105"],
            "docker-compose.proxy.yaml": ["127.0.0.1:8088:8080"],
            "nginx-compose.yaml": ["127.0.0.1:8088:80"],
        }
        for rel, expected in cases.items():
            with self.subTest(file=rel):
                self.assertEqual(self._published_ports(rel), expected)

    def test_no_port_published_on_all_interfaces(self):
        for rel in ["docker-compose.fusional.yaml", "docker-compose.next-server.example.yaml",
                    "docker-compose.proxy.yaml", "nginx-compose.yaml"]:
            for port in self._published_ports(rel):
                with self.subTest(file=rel, port=port):
                    self.assertTrue(port.startswith("127.0.0.1:"), port)


if __name__ == "__main__":
    unittest.main()
