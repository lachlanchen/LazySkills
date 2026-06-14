---
name: jlcpcb-ordering
description: Use when preparing, checking, submitting, documenting, or troubleshooting JLCPCB/JiaLiChuang PCB orders from Gerber ZIPs, including China/global site workflows, desktop assistant handoff, Chrome CDP automation, private config, OSP/surface-finish limits, quality-compensation fees, courier defaults, and review-before-payment submission.
---

# JLCPCB Ordering

## Overview

Use this skill to turn a checked Gerber ZIP into a guarded JLC order workflow. Keep public repos clean: never commit recipient names, phone numbers, addresses, cookies, OTP/SMS codes, screenshots with private fields, wallet/payment data, or `~/.config/jlcpcb-order/private.json`.

## Safety Rules

- Treat submit/payment controls as real-world actions. Do not click final submit without explicit user intent, and never click recharge, wallet, or payment buttons unless the user explicitly asks.
- Stop if the order-check drawer shows `检测到您的订单还有`, `去填写`, `系统未检测到`, `余额不足`, `充值`, an OSP-size warning, or a paid `品质赔付费`.
- For bare PCBs, use `按标准合同常规处理`; do not select `元器件移植全额赔付`.
- Default China courier is `顺丰电商标快`; default shipping mode is `不同交期订单不一起发货`.

## AgenticApp Tooling

When working in AgenticApp, prefer the maintained CDP tool:

```bash
agentic_tools/jlcpcb_order_agent/scripts/launch_shared_chrome.sh
agentic_tools/jlcpcb_order_agent/scripts/quick_order_china.sh path/to/gerber.zip
agentic_tools/jlcpcb_order_agent/scripts/quick_order_global.sh path/to/gerber.zip
agentic_tools/jlcpcb_order_agent/scripts/quick_order_assistant.sh path/to/gerber.zip
```

Use `JLCPCB_ALLOW_SUBMIT=1` only after the check drawer is clean. Private state lives under `~/.config/jlcpcb-order/`: config, DOM snapshots, SQLite order database, and completion logs.

## Workflow

1. Validate the board package first: KiCad DRC/ERC, Gerber ZIP, drill files, board size, and preview.
2. Launch the shared logged-in Chrome profile through CDP; do not create throwaway browser profiles for ordering.
3. Upload Gerbers and fill conservative bare-PCB defaults: FR-4, low quantity, no SMT, no stencil, manual confirmation, standard compensation.
4. If OSP is rejected because any side is under `7 cm`, choose a supported finish such as lead-free HASL or stop for review.
5. Run `检查订单`, clear all missing fields, record a private snapshot, then submit only to review/payment boundary when authorized.
6. After success, record `pcbPlaceSuccess` or global order-success pages in the private database and stop before payment.

Read `references/jlcpcb-ordering-runbook.md` for live DOM selectors, terms, and the China/global/assistant submission paths.
