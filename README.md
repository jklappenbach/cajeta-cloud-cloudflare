# cajeta-cloud-cloudflare

The Cloudflare adapters for [`dev.cajeta.cloud`](https://github.com/jklappenbach/cajeta-cloud)'s
ports, written in Cajeta:

| Port | Adapter | Status |
|---|---|---|
| object store | R2 through the shared S3 client, [cajeta-cloud-s3](https://github.com/jklappenbach/cajeta-cloud-s3) | `R2ObjectStore.connect(bucket, config)` |
| identity (`TokenVerifier`) | Cloudflare Access application tokens; every other identity operation refuses | `IDENTITY_PROVIDER=access` |
| queue | Cloudflare Queues (pull consumers) | planned |
| key-value | Workers KV | planned |

Configuration comes from a `CloudflareConfig` component first, then the
environment: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` (the REST APIs),
`R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` (R2's S3 API), and the optional
`R2_JURISDICTION` (`eu`, `fedramp`). A service can have its own token through
`CloudflareConfig.tokenFor(service, token)` or `CLOUDFLARE_<SERVICE>_API_TOKEN`.
A missing value fails at configuration naming the field and the variable;
no message carries a value.

```cajeta
import dev.cajeta.cloud.cloudflare.R2ObjectStore;
import dev.cajeta.cloud.s3.S3ObjectStore;

S3ObjectStore assets #= R2ObjectStore.connect("assets", null);   // account and keys from the environment
```

R2 differs from S3 in what the port permits, and the adapter says so as an
`S3Profile` rather than a branch on the hostname: every part of a multipart
upload but the last is the same size, 5 MiB at least (the streaming writer
keeps this by construction); `TooManyRequests` is transient; conditional
writes (`putIfAbsent`, `putIfMatch`) are declared only with
`R2_CONDITIONAL_WRITES=1`, until the spec's Q1 is verified against a real
bucket, and refuse cleanly otherwise. The skill `cloudflare-r2-object-store`
covers the adapter's behaviour.

Access forwards each request with a signed JWT; the `access` identity adapter
verifies it (`AccessRequests.verify(verifier, request)` reads
`Cf-Access-Jwt-Assertion` or the `CF_Authorization` cookie) against the
team's certificate set, cached through the shared `JwksCache`, and turns it
into the port's claims with the subject, email and forwarded groups. It takes
`CLOUDFLARE_ACCESS_TEAM` and `CLOUDFLARE_ACCESS_AUD`, no secret, and refuses
registration, sign-in and every other identity operation as unsupported.
The skill `cloudflare-access-identity` covers it.

**Status: in development (0.1.0 unreleased).** The spec and plan are
`cajeta-cloud-cloudflare` in the cajeta repository's `specs/` and `agents/`.

## Build and test

```sh
./run-tests.sh
```

The suite needs no Cloudflare account: R2 runs against `FakeS3` from
cajeta-cloud-s3 with R2's part rule enforced, and the object-store
conformance suite runs over it under both profiles; Access runs against a
fixture certificate set and tokens signed by it. The same suite runs
against a real bucket when `CAJETA_R2_TEST_BUCKET` is set, with the chain's
variables; `cloudflare-live.yml` does that on dispatch and fails if the live
leg skips. Dependency archives resolve from `~/.olla` or Olla at the versions
`cajeta.json` pins; `cajeta-cloud-s3` builds from a sibling checkout
(`S3_REPO`) until it is published; `CLOUD_CJA=`, `S3_CJA=` and the like
override one with a local build.

## License

Apache-2.0.
