---
id: cloudflare-r2-object-store
applies-to: [dev/cajeta/cloud/cloudflare/R2ObjectStore, dev/cajeta/cloud/cloudflare/CloudflareChain, dev/cajeta/cloud/cloudflare/CloudflareConfig, dev/cajeta/cloud/cloudflare/R2Errors]
title: Cloudflare R2 behind the object-store port
description: Build an S3ObjectStore for an R2 bucket from the Cloudflare configuration chain; what the R2 profile declares, excludes and rules differently from S3.
---

# R2 through the Cloudflare chain

The S3 client is `dev.cajeta.cloud.s3` (skill `s3-object-store`), shared with
every S3-compatible provider. `cajeta-cloud-cloudflare` adds the R2 way of
building one: the endpoint from the account, the keys from the chain, and the
R2 profile.

```cajeta
import dev.cajeta.cloud.cloudflare.CloudflareConfig;
import dev.cajeta.cloud.cloudflare.R2ObjectStore;
import dev.cajeta.cloud.s3.S3ObjectStore;

// Account id and R2 keys from the environment
S3ObjectStore assets #= R2ObjectStore.connect("assets", null);

// Or declared by the application; null fields defer to the environment
CloudflareConfig cfg = heap CloudflareConfig("<account id>", null, "<r2 key id>", "<r2 secret>");
cfg.jurisdiction("eu");                                     // https://<account>.eu.r2.cloudflarestorage.com
S3ObjectStore eu #= R2ObjectStore.connect("assets", cfg);
```

The chain is `CloudflareConfig` first, then `CLOUDFLARE_ACCOUNT_ID`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and the optional `R2_JURISDICTION`
(`eu` or `fedramp`; anything else is refused by name). A missing value throws
`CloudflareConfigurationException` naming the config field and the variable;
`connect` itself calls nothing. The endpoint is
`https://<account>.r2.cloudflarestorage.com` (or `<account>.<jurisdiction>.`),
signed for region `auto`, bucket in the path.

## What the R2 profile says

- **Multipart**: every part but the last the same size, 5 MiB at least. The
  streaming writer (`openWrite`) keeps this by construction; a hand-built
  `beginMultipart` upload with unequal parts is refused by R2 at `complete`
  with `InvalidPart`, by S3 and R2 alike below 5 MiB with `EntityTooSmall`.
  The default part size is 5 MiB; `connect(bucket, config, partSize)` takes a
  larger one and refuses a smaller one at open.
- **Conditional writes**: `putIfAbsent` and `putIfMatch` are *not declared*
  until the spec's Q1 (does R2 honour `If-None-Match: *` and `If-Match` on
  PutObject?) is verified against a real bucket. They refuse cleanly per the
  parent's §3.2, naming `object.conditional-put-create` and the adapter `r2`.
  `R2_CONDITIONAL_WRITES=1` declares them; the live conformance leg runs the
  conditional and concurrent-writers cases under that flag.
- **Errors** map through the shared S3 table with R2's own entries:
  `TooManyRequests` (429) is transient, `NotImplemented` (501, an S3 feature
  R2 lacks) a provider error naming the feature. `R2Errors.kindOf` is the
  table; the profile carries it into the store.
- **Not operations of the port**, so nothing can ask for them: object lock,
  ACLs, SSE-KMS, the checksum algorithms R2 does not support.

## Testing without an account

`FakeS3` (cajeta-cloud-s3 testkit) with `fake.partRule(5242880L, true)`
enforces R2's rule; build the store as
`heap S3ObjectStore(fake, bucket, 5242880L, R2ObjectStore.profile(false))`
and run `ObjectStoreContract.verify`. Against a real bucket set
`CAJETA_R2_TEST_BUCKET` with the chain's variables.
