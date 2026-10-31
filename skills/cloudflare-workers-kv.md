---
id: cloudflare-workers-kv
applies-to: [dev/cajeta/cloud/cloudflare/CloudflareKeyValue, dev/cajeta/cloud/cloudflare/KvWrite, dev/cajeta/cloud/cloudflare/KvErrors, dev/cajeta/cloud/cloudflare/HttpKvApi]
title: Workers KV behind the key-value port — selecting, configuring and using the `cloudflare` key-value adapter
description: Select the Workers KV adapter with KV_PROVIDER=cloudflare, give it the account, namespace and token, and know how writes with metadata and expiry, reads, listing, bulk calls, eventual consistency, missing conditional writes and KV's limits behave.
---

# Workers KV through the port

```cajeta
import dev.cajeta.cloud.kv.KeyValueSelector;
import dev.cajeta.cloud.kv.KeyValueStore;
import dev.cajeta.cloud.kv.PutOptions;

KeyValueSelector s = KeyValueSelector.__cajeta_inject();   // KV_PROVIDER=cloudflare
KeyValueStore kv = s.store();
PutOptions o = heap PutOptions();
o.metadata("{\"owner\":\"ada\"}");
o.timeToLive(3600L);                                       // 60 s at least
kv.put("session:42", bytes, o);
KvEntry e #= kv.get("session:42");                         // null when absent or expired
```

The adapter configures itself on first use from `CLOUDFLARE_ACCOUNT_ID`,
`CLOUDFLARE_KV_NAMESPACE_ID` and the kv token of the chain
(`CLOUDFLARE_KV_API_TOKEN`, else `CLOUDFLARE_API_TOKEN`; a
`CloudflareConfig` component's `tokenFor("kv", ...)` or shared token first).
For a store you built yourself,
`CloudflareKeyValue.over(heap HttpKvApi(account, namespaceId, token))`.

## How the port maps

- **put** is a value write (`PUT values/<key>`; multipart with a `metadata`
  part when metadata is set) with `expiration` or `expiration_ttl`. The
  port's metadata is an opaque string and KV's is JSON, so it travels as a
  JSON string literal and reads back as the same string.
- **get** lists the key (`GET keys?prefix=<key>&limit=1`) for its expiration
  and metadata, then reads the value; null when the key is absent or
  expired. KV has no version, so `KvEntry.version()` is derived from the
  bytes: two reads of the same bytes agree, a changed value differs.
- **delete** reports whether the key existed (KV answers 404 otherwise).
- **list(prefix, cursor, limit)** pages through `GET keys`. KV's smallest
  page is 10, so a smaller limit is paged by the adapter: the keys past the
  limit ride in the cursor and are served before the server is asked again.
  Cursors are opaque; "" is the end.
- **putAll(ArrayList<KvWrite>)** and **deleteAll(ArrayList<String>)** are
  the adapter's own bulk calls (`PUT bulk`, `DELETE bulk`), 10,000 pairs a
  call; the port has no bulk surface. Pass `#options` into a `KvWrite`.

## Capabilities and consistency

Declared: `kv.metadata` (JSON up to 1024 B) and `kv.expiry` (an absolute
expiration or a TTL of 60 s or more). Not declared: `kv.conditional-create`
and `kv.compare-and-set` (KV has no conditional write; `putIfAbsent` and
`compareAndSet` refuse PROVIDER_ERROR naming the capability, before any
request), `kv.strong-consistency` and `kv.read-your-writes`. The store is
eventual with `propagationBoundSeconds()` of 60, Cloudflare's documented
bound: a read within a minute of a write may see the prior value.

## Limits and errors

Refused by name before a request (PROVIDER_ERROR): an empty key or one over
512 bytes, a value over 25 MiB (26214400 bytes), metadata over 1024 bytes, a
TTL under 60 s. A 429 (KV allows one write a second a key) is TRANSIENT and
retried under `RetryPolicy.standard`; a 5xx likewise; 401/403 is
ACCESS_DENIED; 404 NOT_FOUND.

## Testing without an account

`dev.cajeta.cloud.cloudflare.testkit.FakeKvApi(clock)` answers the REST
endpoints in process; `fake.lag(seconds)` delays the visibility of every
write and delete so the eventual model is exercised, `rateLimitNext(n)`
stages 429s. `CloudflareKeyValue.over(fake)` with a `ManualWaiter` runs
`KeyValueContract`. Against a real namespace set
`CAJETA_KV_TEST_NAMESPACE_ID` with the chain's variables.
