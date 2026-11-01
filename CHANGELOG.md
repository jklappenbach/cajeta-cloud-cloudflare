# Changelog

## 0.2.0

On `dev.cajeta.cloud` 0.6.0, whose memory drivers are now `memory` components, and `dev.cajeta.cloud.s3` 0.1.1, whose stores keep their transport. Every R2 store from 0.1.0 read a freed transport on its first request.

- R2 is the `cloudflare` object-store component, `CloudflareObjectStore`, so `OBJECT_STORE_PROVIDER=cloudflare` selects it. It connects on first use to the bucket `R2_BUCKET` names and refuses, naming the variable, when it is unset.
- `CLOUDFLARE_API_BASE_URL` points the Queues and KV adapters at another REST base URL, `R2_ENDPOINT` points R2 at another S3 endpoint, and `CLOUDFLARE_ACCESS_CERTS_URL` points Access at another certificate set. Each defaults to Cloudflare's own. `HttpQueuesApi.at` and `HttpKvApi.at` take a base URL in code.
- `FakeCloudflareServer` in the testkit serves the Queues, KV, R2 and Access certificate endpoints over HTTP from the in-process fakes, so a program configured only from the environment can run against them.
- A program with these adapters compiled in now holds two implementations of each port, so outside a test or dev profile it must name every provider.

## 0.1.0 (2026-11-01)

- R2 behind the object-store port: `R2ObjectStore.connect(bucket, config)` derives the endpoint from the account id and optional jurisdiction (`eu`, `fedramp`), signs for region `auto` in path style, and opens the shared `S3ObjectStore` under the R2 profile: equal 5 MiB parts but the last, R2's own error codes, conditional writes undeclared until spec Q1 (`R2_CONDITIONAL_WRITES=1` declares them).
- Configuration: `CloudflareConfig` first, then `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_JURISDICTION`; a service's own token through `tokenFor` or `CLOUDFLARE_<SERVICE>_API_TOKEN`; a missing value is a `CloudflareConfigurationException` naming it.
- Cloudflare Access behind the identity port: the `access` adapter verifies the tokens Access forwards (RS256 against the team's certificate set through the shared `JwksCache`, `iss`, `aud`, `nbf`, `exp`; each failed check named, never the token), `AccessRequests` reads the header or the `CF_Authorization` cookie, `AccessPrincipal` tells a service token from a user; every other identity operation refuses as unsupported. Configured by `AccessConfig` or `CLOUDFLARE_ACCESS_TEAM` and `CLOUDFLARE_ACCESS_AUD`.
- Cloudflare Queues behind the queue port: the `cloudflare` adapter sends through the REST API (the port's JSON envelope carries the attributes), receives through the HTTP pull consumer with the lease id as the receipt, acks and retries in one call per batch; a queue without a pull consumer fails the first receive naming the setting; the 128 KiB, 100-message and 12-hour limits are refused by name and a rate limit is retried under `RetryPolicy`. `FakeQueuesApi` in the testkit.
- Workers KV behind the key-value port: the `cloudflare` adapter writes with metadata (as a JSON string) and expiry, reads value and metadata, deletes, lists behind KV's cursor (a limit under KV's minimum of 10 is paged by the adapter), and adds `putAll` / `deleteAll` through the bulk endpoints; declares `kv.metadata`, `kv.expiry` and eventual consistency with the 60-second bound, no conditional writes; the 512 B key, 25 MiB value, 1024 B metadata and 60 s TTL limits are refused by name and a rate limit is retried. `FakeKvApi` in the testkit with a propagation lag.
