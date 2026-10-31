---
id: cloudflare-queues
applies-to: [dev/cajeta/cloud/cloudflare/CloudflareQueue, dev/cajeta/cloud/cloudflare/QueuesJson, dev/cajeta/cloud/cloudflare/QueuesErrors, dev/cajeta/cloud/cloudflare/HttpQueuesApi]
title: Cloudflare Queues behind the queue port — selecting, configuring and using the `cloudflare` queue adapter
description: Select the Cloudflare Queues adapter with QUEUE_PROVIDER=cloudflare, give it the account, queue id and token, and know how sending, the HTTP pull consumer, leases, acks, retries, the message envelope, limits and rate limits behave.
---

# Cloudflare Queues through the port

```cajeta
import dev.cajeta.cloud.queue.MessageQueue;
import dev.cajeta.cloud.queue.QueueSelector;

QueueSelector s = QueueSelector.__cajeta_inject();     // QUEUE_PROVIDER=cloudflare
MessageQueue q = s.queue();
String id #= q.send(bytes, attributes, 0L);
Received r #= q.receive(10, 30L);                      // up to 10, a 30 s visibility window
q.ack(r.messageAt(0).receipt());                       // the receipt is the lease id
```

The adapter configures itself on first use from `CLOUDFLARE_ACCOUNT_ID`,
`CLOUDFLARE_QUEUE_ID` and the queues token of the chain
(`CLOUDFLARE_QUEUES_API_TOKEN`, else `CLOUDFLARE_API_TOKEN`; a
`CloudflareConfig` component's `tokenFor("queues", ...)` or shared token
first). Construction does nothing. For a queue you built yourself,
`CloudflareQueue.over(heap HttpQueuesApi(account, queueId, token))`.

## How the port maps

- **send / sendBatch** call the REST send and batch endpoints; a delay is
  `delay_seconds`. Queues has no message attributes, so every message
  travels in the port's envelope, `{"attributes":{...},"body":"<base64>"}`
  with content type `json`; a Worker consuming the same queue reads
  `message.body.attributes` and decodes `message.body.body`. A body that is
  not an envelope (another producer's) arrives as its own bytes with no
  attributes.
- **receive(max, visibility)** is the HTTP pull consumer: `batch_size` and
  `visibility_timeout_ms`. The queue must have an HTTP pull consumer
  configured; without one the first receive fails PROVIDER_ERROR naming the
  setting. The receipt is the message's `lease_id`; `attempt` is the API's
  `attempts`; `sentAtSeconds` its `timestamp_ms`.
- **ack / ackAll / release** go to the ack endpoint, batching what the
  caller batched: acks as `acks`, a release as one `retries` entry with its
  `delay_seconds`. A lease the API did not count (expired, or another
  queue's) is PRECONDITION_FAILED; the message may already be with another
  consumer.

## Capabilities and limits

Declared: `queue.delayed-send` (up to 12 hours) and
`queue.dead-letter-reporting` (the attempt count; the dead-letter queue is
the queue's own setting). Not declared, so never assumed: FIFO,
exactly-once, message groups.

Refused by name before any request (PROVIDER_ERROR): a body over 128 KiB
(131072 bytes), a batch or a pull over 100 messages, a delay or visibility
over 43200 s. A 429 from the API is TRANSIENT and retried under
`RetryPolicy.standard` (four attempts, jittered backoff; `stats().retries()`
counts them); a 5xx likewise; 401/403 is ACCESS_DENIED, 404 NOT_FOUND. The
API's own refusal of a body names the limit in the message.

## Testing without an account

`dev.cajeta.cloud.cloudflare.testkit.FakeQueuesApi(clock)` answers the four
endpoints in process with leases and visibility on a `TimeSource`;
`CloudflareQueue.over(fake)` with a `ManualWaiter` runs `QueueContract`.
`withoutPullConsumer()`, `rateLimitNext(n)` and `refuseNextAsTooLarge()`
stage the error shapes. Against a real queue set
`CAJETA_QUEUES_TEST_QUEUE_ID` with the chain's variables.
