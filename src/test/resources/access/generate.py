# Access-shaped fixtures (cajeta-cloud-cloudflare spec 4): a team's certificate
# set and application tokens as Cloudflare Access signs them, RS256 with a
# `kid`, `iss` the team domain, `aud` an array holding the application's AUD
# tag, `type` "app", `nbf`/`iat`/`exp`, `email` and `sub` for a user, and
# `common_name` with an empty `sub` for a service token. The keys are random,
# so the fixtures were generated once and are committed; this is not rerun.
import json, base64, os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
out = os.path.dirname(os.path.abspath(__file__))
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def i2b(n): return n.to_bytes((n.bit_length()+7)//8, "big")
keys = {k: rsa.generate_private_key(public_exponent=65537, key_size=2048)
        for k in ["access-kid-1", "access-kid-2", "rotated-kid-3"]}
def jwk(kid):
    pn = keys[kid].public_key().public_numbers()
    return {"kid": kid, "kty": "RSA", "alg": "RS256", "use": "sig", "e": b64(i2b(pn.e)), "n": b64(i2b(pn.n))}
TEAM = "example-team"
ISS = f"https://{TEAM}.cloudflareaccess.com"
AUD = "f5a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80"
SUB = "6d3f5b1e-2a4c-4f8e-9b0d-1c2e3f4a5b6c"
IAT = 1767225600; EXP = IAT + 86400
def sign(kid, payload):
    h = b64(json.dumps({"alg": "RS256", "kid": kid, "typ": "JWT"}, separators=(",", ":")).encode())
    p = b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = keys[kid].sign(f"{h}.{p}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{h}.{p}.{b64(sig)}"
def user(**over):
    c = {"aud": [AUD], "email": "ada@example.com", "exp": EXP, "iat": IAT, "nbf": IAT,
         "iss": ISS, "type": "app", "identity_nonce": "6ZxVbWsq2xNfj8Qb", "sub": SUB,
         "country": "GB", "groups": ["admins", "editors"],
         "custom": {"department": "engines"}}
    c.update(over); return c
def service(**over):
    c = {"aud": [AUD], "exp": EXP, "iat": IAT, "nbf": IAT, "iss": ISS, "type": "app",
         "common_name": "3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d.access", "sub": ""}
    c.update(over); return c
files = {
  "certs.json": json.dumps({"keys": [jwk("access-kid-1"), jwk("access-kid-2")], "public_cert": {"kid": "access-kid-1", "cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"}, "public_certs": []}),
  "certs-rotated.json": json.dumps({"keys": [jwk("access-kid-1"), jwk("access-kid-2"), jwk("rotated-kid-3")], "public_certs": []}),
  "user.jwt": sign("access-kid-1", user()),
  "user-second-key.jwt": sign("access-kid-2", user()),
  "service.jwt": sign("access-kid-1", service()),
  "user-wrong-issuer.jwt": sign("access-kid-1", user(iss="https://other-team.cloudflareaccess.com")),
  "user-wrong-aud.jwt": sign("access-kid-1", user(aud=["0000000000000000000000000000000000000000000000000000000000000000"])),
  "user-two-auds.jwt": sign("access-kid-1", user(aud=["0000000000000000000000000000000000000000000000000000000000000000", AUD])),
  "user-not-yet-valid.jwt": sign("access-kid-1", user(nbf=IAT + 3600)),
  "user-rotated-key.jwt": sign("rotated-kid-3", user()),
  "user-no-groups.jwt": sign("access-kid-1", {k: v for k, v in user().items() if k != "groups"}),
}
t = files["user.jwt"].split(".")
files["user-forged.jwt"] = ".".join([t[0], b64(json.dumps(user(email="mallory@example.com"), separators=(",", ":")).encode()), t[2]])
for name, text in files.items():
    open(f"{out}/{name}", "w").write(text)
print(json.dumps({"team": TEAM, "iss": ISS, "aud": AUD, "sub": SUB, "iat": IAT, "exp": EXP}))
