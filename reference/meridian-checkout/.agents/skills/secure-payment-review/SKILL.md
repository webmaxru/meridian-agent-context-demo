---
name: secure-payment-review
description: Review Meridian checkout changes for payment-safety and reliability risks. Use when reviewing payment, refund, retry, or transaction-handling code.
license: MIT
metadata:
  author: Meridian Platform Engineering
  version: "1.0.0"
  owner: platform-security
---

# Secure Payment Review

Review only the changed payment flow and report concrete findings with file and line references.

## Required checks

1. Represent money with Meridian's `Money` value object; never use floating-point currency math.
2. Make checkout, capture, and refund retries idempotent by `paymentAttemptId`.
3. Never log card data, authorization headers, access tokens, or raw payment-provider payloads.
4. Validate state transitions before capture or refund operations.
5. Treat timeouts as an unknown outcome until the provider confirms the transaction state.

## Output

Return findings ordered by severity. For every finding, state the failure mode, the affected code,
and the smallest safe correction. Say `No payment-safety findings` when all required checks pass.
