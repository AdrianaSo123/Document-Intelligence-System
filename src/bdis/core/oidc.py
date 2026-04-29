from __future__ import annotations

import base64
import json
import time
import hmac
import hashlib
from dataclasses import dataclass
from typing import Any

import httpx
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes


def _b64url_decode(data: str) -> bytes:
    padding_len = (-len(data)) % 4
    data_padded = data + ("=" * padding_len)
    return base64.urlsafe_b64decode(data_padded.encode("utf-8"))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _parse_jwt(token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    header_b64, payload_b64, sig_b64 = parts
    header = json.loads(_b64url_decode(header_b64))
    payload = json.loads(_b64url_decode(payload_b64))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = _b64url_decode(sig_b64)
    return header, payload, signature, signing_input.decode("utf-8")


def _rsa_public_key_from_jwk(jwk: dict[str, Any]) -> rsa.RSAPublicKey:
    if jwk.get("kty") != "RSA":
        raise ValueError("Unsupported JWK kty")
    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    public_numbers = rsa.RSAPublicNumbers(e=e, n=n)
    return public_numbers.public_key()


@dataclass
class JwksCache:
    jwks_url: str
    ttl_seconds: int = 300
    _cached_at: float = 0.0
    _keys_by_kid: dict[str, dict[str, Any]] | None = None

    def get(self) -> dict[str, dict[str, Any]]:
        now = time.time()
        if self._keys_by_kid and (now - self._cached_at) < self.ttl_seconds:
            return self._keys_by_kid
        r = httpx.get(self.jwks_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        keys = data.get("keys", [])
        self._keys_by_kid = {k.get("kid"): k for k in keys if k.get("kid")}
        self._cached_at = now
        return self._keys_by_kid


def verify_jwt(
    token: str,
    alg: str,
    secret: str | None = None,
    jwks_cache: JwksCache | None = None,
    issuer: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    header, payload, signature, signing_input_str = _parse_jwt(token)
    signing_input = signing_input_str.encode("utf-8")

    token_alg = header.get("alg")
    if token_alg != alg:
        raise ValueError("JWT alg mismatch")

    if alg == "HS256":
        if not secret:
            raise ValueError("Missing HS256 secret")
        expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid HS256 signature")
    elif alg == "RS256":
        if not jwks_cache:
            raise ValueError("Missing JWKS cache for RS256")
        kid = header.get("kid")
        if not kid:
            raise ValueError("Missing kid")
        jwk = jwks_cache.get().get(kid)
        if not jwk:
            raise ValueError("Unknown kid")
        pub = _rsa_public_key_from_jwk(jwk)
        pub.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    else:
        raise ValueError("Unsupported JWT alg")

    # Basic claim checks
    now = int(time.time())
    exp = payload.get("exp")
    if exp is not None and int(exp) < now:
        raise ValueError("JWT expired")
    if issuer and payload.get("iss") != issuer:
        raise ValueError("JWT issuer mismatch")
    if audience:
        aud = payload.get("aud")
        if isinstance(aud, list):
            if audience not in aud:
                raise ValueError("JWT audience mismatch")
        elif aud != audience:
            raise ValueError("JWT audience mismatch")

    return payload

