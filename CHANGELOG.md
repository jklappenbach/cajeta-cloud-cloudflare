# Changelog

## 0.1.0 (unreleased)

- R2 behind the object-store port: `R2ObjectStore.connect(bucket, config)` derives the endpoint from the account id and optional jurisdiction (`eu`, `fedramp`), signs for region `auto` in path style, and opens the shared `S3ObjectStore` under the R2 profile: equal 5 MiB parts but the last, R2's own error codes, conditional writes undeclared until spec Q1 (`R2_CONDITIONAL_WRITES=1` declares them).
- Configuration: `CloudflareConfig` first, then `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_JURISDICTION`; a service's own token through `tokenFor` or `CLOUDFLARE_<SERVICE>_API_TOKEN`; a missing value is a `CloudflareConfigurationException` naming it.
- Cloudflare Access behind the identity port: the `access` adapter verifies the tokens Access forwards (RS256 against the team's certificate set through the shared `JwksCache`, `iss`, `aud`, `nbf`, `exp`; each failed check named, never the token), `AccessRequests` reads the header or the `CF_Authorization` cookie, `AccessPrincipal` tells a service token from a user; every other identity operation refuses as unsupported. Configured by `AccessConfig` or `CLOUDFLARE_ACCESS_TEAM` and `CLOUDFLARE_ACCESS_AUD`.
