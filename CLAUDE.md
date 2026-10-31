# cajeta-cloud-cloudflare

The Cloudflare adapters for dev.cajeta.cloud (package
`dev.cajeta.cloud.cloudflare`): R2 behind the object store through the shared
S3 client (`dev.cajeta.cloud.s3`, sibling `cajeta-cloud-s3`), Cloudflare
Access as a token verifier, Queues behind the queue port, Workers KV behind
the key-value port. Spec and plan: `specs/cajeta-cloud-cloudflare-spec.md`
and `agents/cajeta-cloud-cloudflare-plan.md` in the cajeta repository; this
repo carries no specs of its own.

## Build & test

```sh
./run-tests.sh      # resolves dependency archives, builds the .cja, runs @Test discovery
```

No test reaches Cloudflare by default: R2 runs against `FakeS3` with R2's
part rule switched on; Access against the fixture certificate set and tokens
under `src/test/resources/access` (generated once by `generate.py` there,
never regenerated). The live legs opt in through `CAJETA_R2_TEST_BUCKET`
and the chain's variables (`cloudflare-live.yml`). `cajeta-cloud-s3` builds
from a sibling checkout (`S3_REPO`) until its Olla publish is bound (spec
Q5); `cajeta-cloud` 0.5.1 resolves from Olla (a sibling, `CLOUD_REPO`, only
when the pin is not in `~/.olla`).

## Rules

- Test first: the failing test before the implementation, every change.
- Nothing logs a credential. A missing value fails at configuration naming
  the config field and the variable, never a value.
- A difference between R2 and S3 is an `S3Profile` entry (a capability
  excluded, a part rule, an error code), never a branch on the hostname.
- Conditional writes on R2 stay undeclared until spec Q1 is verified against
  a real bucket; `R2_CONDITIONAL_WRITES=1` declares them.
- Releases ship from the `release` branch; CI's guard refuses a tag not on it.
