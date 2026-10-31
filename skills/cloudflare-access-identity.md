---
id: cloudflare-access-identity
applies-to: [dev/cajeta/cloud/cloudflare/AccessIdentity, dev/cajeta/cloud/cloudflare/AccessTokenVerifier, dev/cajeta/cloud/cloudflare/AccessRequests, dev/cajeta/cloud/cloudflare/AccessConfig, dev/cajeta/cloud/cloudflare/AccessPrincipal]
title: Cloudflare Access behind the identity port — verifying the tokens Access forwards
description: Select the access adapter, give it the team domain and AUD tag, verify the Cf-Access-Jwt-Assertion token on a request, and know that every other identity operation refuses.
---

# Access as a token verifier

Access signs users in itself, through the team's identity providers, and
forwards each request with a signed JWT. The adapter's whole job is to verify
that token: it is the identity port's `TokenVerifier`, and nothing else.

```cajeta
import dev.cajeta.cloud.cloudflare.AccessRequests;
import dev.cajeta.cloud.identity.Claims;
import dev.cajeta.cloud.identity.IdentitySelector;

IdentitySelector s = IdentitySelector.__cajeta_inject();      // IDENTITY_PROVIDER=access
Claims c #= AccessRequests.verify(s.pool().verifier(), request);
if (c == null) { /* no token: unauthenticated, not an error */ }
```

Configuration is `AccessConfig(teamDomain, aud)` as a component, else
`CLOUDFLARE_ACCESS_TEAM` and `CLOUDFLARE_ACCESS_AUD` (spec 7.3); there is no
secret. The team may be given as `example-team`,
`example-team.cloudflareaccess.com` or the URL; the issuer is always
`https://<team>.cloudflareaccess.com` and the certificate set is fetched from
`<issuer>/cdn-cgi/access/certs`.

## What verify checks

In order: a compact RS256 JWT; a `kid` in the team's certificate set (fetched
through the shared `JwksCache`: cached for its Cache-Control lifetime, an
unknown kid refetched once then not again for a minute); the signature;
`iss` equal to the issuer; `nbf` not after now; `exp` after now; `aud` (an
array on Access tokens) holding the AUD tag. A failure is
`IdentityException` INVALID_TOKEN whose message names the check (`issuer`,
`audience`, `not-before`, `expiry`, `signature`, `key`) and never the token.
Access has one token kind, so the expected use is not checked and the claims
report ACCESS.

The claims carry `sub`, `email`, `country`, `identity_nonce` and the rest as
strings, `aud` as the tag, and the token's `groups` array as the port's
groups when the identity provider's groups are forwarded.
`AccessPrincipal.of(claims)` tells a user from a service token: a service
token has `common_name` (its client id) and an empty subject.

## Requests

`AccessRequests.tokenOf(request)` reads `Cf-Access-Jwt-Assertion`, else the
`CF_Authorization` cookie, else null. `AccessRequests.verify(verifier,
request)` returns the claims, null for a request with no token, and throws
for a token that fails.

## Everything else refuses

`register`, `signIn`, `refresh`, `changePassword`, `enrollTotp` and every
other UserPool, Authenticator and Account operation throw
UNSUPPORTED_CAPABILITY naming the adapter `access` and the operation, before
any request. The capabilities declare `identity.jwks` only.

## Testing without an account

`AccessIdentity.over(config, source, clock)` takes any `JwksSource` and
`TimeSource`; the suite serves `src/test/resources/access/certs.json` and the
tokens `generate.py` there signed, on a `ManualTimeSource`.
