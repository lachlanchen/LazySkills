# Multilingual Sticker Storefronts

Keep public products separate from private review galleries and WeChat operations.
An accepted animation can have Chinese, English and Japanese text editions;
these are versions of one sticker, not distinct animations for a different pack.

## Artwork

1. Export from the approved clean animation, not from a GIF with old text baked in.
2. Translate the intended everyday meaning. Review short labels, available font
   glyphs, face clearance, gesture extremes and chat-scale readability.
3. Preserve original, compact, edge and rejected variants. A storefront edition
   does not authorize changing an already-submitted WeChat album.
4. Use web-specific limits transparently. A higher-palette GIF above WeChat's
   upload limit can be a good web download but is not a verified platform upload.
5. Build the catalog from an explicit selected-artwork allowlist. Exclude private
   sidecars, account pages, bank information and production receipts.
6. Provide one content-addressed ZIP per language and check each ZIP's file hashes.
   Capture the full gallery and individual GIF previews in the existing CDP tab.

## Optional Support Price

- Keep the default affordable pack price visible.
- A $1–$99 slider may be paired with a numeric field for higher amounts and cents.
- Validate integer cents on the server, including provider limits. Reject invalid
  values and make the final payment page show the selected currency and amount.
- Any accepted amount unlocks the same advertised languages. Describe the extra
  payment as optional artist support, not a charitable-tax deduction.

## Payment Integrity

Persist an immutable order before Checkout: amount, currency, pack, product,
environment and artifact hashes. Use an idempotency key for retries. Verify the
provider's actual paid session and line items before access; a redirect is not proof.
Use signed webhooks plus return-page reconciliation, and test both.

Keep the order database, receipt secret and purchased artifacts outside immutable
app releases. Keep credentials and private receipts out of public source. Receipt
tokens belong in fragments/authorization headers rather than server URL queries.
Keep website purchases and WeChat purchases independent.

Check the installed SDK service contract, not only a mock: Stripe Python 16 uses
`client.v1.checkout.sessions.line_items.list(...)`. Normalize Stripe objects with
`to_dict()`. Test real sandbox Checkout and every language download before claiming
payment readiness; never use a live card for an automated smoke test.

## Shipping Evidence

Validate 320px/mobile/desktop layouts in every interface language, including RTL.
Check range/number synchronization, below-minimum amounts and amounts above the
slider maximum. Preserve original GIFs, keep static previews lightweight, and
hash large deployment archives as streams on low-memory hosts.

Record the exact release, own service, site URL and verified sandbox outcomes.
Distinguish a local sync-folder copy from confirmed cloud upload, and catalog
provisioning from a completed real purchase.
