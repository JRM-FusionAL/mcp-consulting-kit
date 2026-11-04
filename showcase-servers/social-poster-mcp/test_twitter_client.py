"""Exercise the real OAuth signer and Twitter payloads without network access."""

import json
from unittest.mock import patch

import pytest
import requests
from requests.adapters import BaseAdapter

from clients.twitter_client import TwitterClient


class RecordingAdapter(BaseAdapter):
    def __init__(self, status=201):
        self.requests = []
        self.status = status

    def send(self, request, **kwargs):
        self.requests.append(request)
        response = requests.Response()
        response.status_code = self.status
        response.request = request
        response._content = json.dumps({"data": {"id": str(len(self.requests))}}).encode()
        return response

    def close(self):
        pass


@pytest.fixture
def signed_client(monkeypatch):
    for name, value in {
        "TWITTER_API_KEY": "test-consumer",
        "TWITTER_API_SECRET": "test-consumer-secret",
        "TWITTER_ACCESS_TOKEN": "test-token",
        "TWITTER_ACCESS_TOKEN_SECRET": "test-token-secret",
    }.items():
        monkeypatch.setenv(name, value)
    client = TwitterClient()
    session = client._session()
    adapter = RecordingAdapter()
    # Both schemes terminate in our adapter; no request can reach the network.
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    with patch.object(client, "_session", return_value=session):
        yield client, adapter
    session.close()


def test_thread_signs_each_request_and_chains_replies(signed_client):
    client, adapter = signed_client
    assert client.post_thread(["First", "Second"]) == [
        {"data": {"id": "1"}}, {"data": {"id": "2"}}
    ]
    assert [json.loads(request.body) for request in adapter.requests] == [
        {"text": "First"},
        {"text": "Second", "reply": {"in_reply_to_tweet_id": "1"}},
    ]
    for request in adapter.requests:
        assert request.url == "https://api.twitter.com/2/tweets"
        assert request.method == "POST"
        auth = request.headers["Authorization"]
        if isinstance(auth, bytes):
            auth = auth.decode()
        assert auth.startswith("OAuth ")
        for field in ["oauth_signature=", "oauth_nonce=", "oauth_timestamp=",
                      'oauth_token="test-token"', 'oauth_consumer_key="test-consumer"']:
            assert field in auth
        assert "test-consumer-secret" not in auth
        assert "test-token-secret" not in auth


def test_http_error_stops_thread(signed_client):
    client, adapter = signed_client
    adapter.status = 403
    with pytest.raises(requests.HTTPError):
        client.post_thread(["First", "Must not be sent"])
    assert len(adapter.requests) == 1


def test_empty_thread_makes_no_request(signed_client):
    client, adapter = signed_client
    assert client.post_thread([]) == []
    assert adapter.requests == []
