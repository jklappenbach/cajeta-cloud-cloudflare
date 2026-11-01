# cajeta-cloud-cloudflare

The Cloudflare adapters for [`dev.cajeta.cloud`](https://github.com/jklappenbach/cajeta-cloud)'s
ports, written in Cajeta:

| Port | Adapter | Status |
|---|---|---|
| object store | R2 through the shared S3 client, [cajeta-cloud-s3](https://github.com/jklappenbach/cajeta-cloud-s3) | `OBJECT_STORE_PROVIDER=cloudflare` with `R2_BUCKET`, or `R2ObjectStore.connect(bucket, config)` |
| identity (`TokenVerifier`) | Cloudflare Access application tokens; every other identity operation refuses | `IDENTITY_PROVIDER=access` |
| queue (`MessageQueue`) | Cloudflare Queues through the REST API and an HTTP pull consumer; the receipt is the lease id | `QUEUE_PROVIDER=cloudflare` |
| key-value (`KeyValueStore`) | Workers KV through the REST API, eventual with a 60 s bound, no conditional writes | `KV_PROVIDER=cloudflare` |

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

The `cloudflare` queue adapter sends through the Queues REST API and
receives through an HTTP pull consumer; messages travel in the port's JSON
envelope so attributes round-trip, acks and retries batch what the caller
batched, Cloudflare's limits are refused by name and a rate limit is
retried. It reads `CLOUDFLARE_QUEUE_ID` and the queues token of the chain.
The skill `cloudflare-queues` covers it.

The `cloudflare` key-value adapter writes, reads, lists and deletes through
the Workers KV REST API with metadata and expiry, adds `putAll` and
`deleteAll` through the bulk endpoints, declares eventual consistency with
Cloudflare's 60-second bound and no conditional writes, refuses KV's limits
by name and retries a rate limit. It reads `CLOUDFLARE_KV_NAMESPACE_ID` and
the kv token of the chain. The skill `cloudflare-workers-kv` covers it.

The memory drivers are compiled in beside these adapters, so a production
build names each provider; a test or dev build can name `memory` in code. A
local fake stands in for Cloudflare when `CLOUDFLARE_API_BASE_URL`,
`R2_ENDPOINT` and `CLOUDFLARE_ACCESS_CERTS_URL` point at the testkit's
`FakeCloudflareServer`. primavera's `cloud-switch` sample runs one service
both ways.

## Capabilities

What each adapter declares (parent spec §3.5); an undeclared capability's
operation refuses by name before any request.

| Adapter | Declared | Not declared |
|---|---|---|
| `r2` object store | `object.multipart` (equal parts but the last, 5 MiB at least), `object.range-read`, `object.list-lexicographic`, `object.read-after-write`, `object.server-side-copy`; `object.conditional-put-create` and `-overwrite` with `R2_CONDITIONAL_WRITES=1` | the conditional puts until spec Q1 is verified |
| `access` identity | `identity.jwks` | everything else: registration, sign-in, passwords, factors, groups, admin |
| `cloudflare` queue | `queue.delayed-send` (up to 12 h), `queue.dead-letter-reporting` (the attempt count) | `queue.fifo`, `queue.exactly-once`, `queue.message-groups` |
| `cloudflare` key-value | `kv.metadata` (JSON, 1024 B), `kv.expiry` (absolute, or a TTL of 60 s or more); eventual with a 60 s `propagationBoundSeconds()` | `kv.conditional-create`, `kv.compare-and-set`, `kv.strong-consistency`, `kv.read-your-writes` |

**Status: 0.1.0 released; 0.2.0 in development.** The spec and plan are
`cajeta-cloud-cloudflare` in the cajeta repository's `specs/` and `agents/`.

## Build and test

```sh
./run-tests.sh
```

The suite needs no Cloudflare account: R2 runs against `FakeS3` from
cajeta-cloud-s3 with R2's part rule enforced, and the object-store
conformance suite runs over it under both profiles; Access runs against a
fixture certificate set and tokens signed by it; Queues against an in-process
REST API with leases on a manual clock; KV against one with a propagation
lag. The same suite runs
against a real bucket when `CAJETA_R2_TEST_BUCKET` is set, with the chain's
variables; `cloudflare-live.yml` does that on dispatch and fails if the live
leg skips. Dependency archives resolve from `~/.olla` or Olla at the versions
`cajeta.json` pins; `cajeta-cloud-s3` builds from a sibling checkout
(`S3_REPO`) until it is published; `CLOUD_CJA=`, `S3_CJA=` and the like
override one with a local build.

## License

Apache-2.0.
