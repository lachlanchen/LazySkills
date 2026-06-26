# JLCPCB Ordering Runbook

## Entry Points

- China web order: `https://www.jlc.com/newOrder/#/pcb/newOnlinePlaceOrder?spm=jlc-pc.newcenterpage.business`
- Global quote: `https://cart.jlcpcb.com/quote?spm=jlcpcb.Public.2006`
- China desktop assistant: prefer `~/.local/bin/jlc-assistant`; legacy system install may be `/opt/jlc-assistant/jlc-assistant`
- Private config: `~/.config/jlcpcb-order/private.json`
- Private database: `~/.config/jlcpcb-order/orders.sqlite3`
- Private DOM snapshots: `~/.config/jlcpcb-order/dom/`

## Live Terms

- `特价`: promotional PCB fabrication base price.
- `喷镀费`: surface-finish/plating fee.
- `品质赔付费`: paid quality-compensation fee; avoid for bare PCB by selecting `按标准合同常规处理`.
- `并单发货`: combined shipment. If SF rejects it, choose `不同交期订单不一起发货`.
- `OSP`: free finish but can be rejected by the China site. A `2.4 cm x 2.4 cm` board was rejected because any side under `7 cm` cannot use OSP there.
- `顺丰电商标快`: default prepaid China courier.

## China Web Defaults

Use conservative bare-PCB defaults unless the user asks otherwise:

- FR-4, 2 layers, quantity 5, 1.6 mm, 1 oz, green solder mask, white silkscreen.
- Surface finish: OSP only if valid for the board size; otherwise use a supported finish such as lead-free HASL after review.
- Standard compensation: `按标准合同常规处理`.
- Explicit dimensions: fill `长` and `宽` in centimeters when the order-check drawer shows `板子尺寸 去填写`.
- Delivery format: `出货方式 -> 单片` for one-board Gerber jobs.
- Board mark/customer code: select `标志增加方式 -> 每个单片内增加`, then `板上加标志 -> 加嘉立创客编（免费）`; handle the `加客编` modal by selecting `每个单片内增加` and clicking `确认`.
- No SMT: `是否SMT贴片 -> 不需要`.
- No stencil: `是否开钢网 -> 不需要`.
- No edge polishing: `是否需要磨边 -> 不需要`.
- Manual confirmation: `手动确认订单`.
- Electronic receipt/delivery note.
- Separate shipment: `不同交期订单不一起发货`.
- Courier: `顺丰电商标快`.

## China DOM Notes

- Upload input: first `input[type=file]`.
- Uploaded-file action: `立即下单`.
- Existing uploaded row: match the Gerber ZIP stem and use that row's `立即下单`/`pcbFileId`; do not upload another copy unless the legacy row is absent or invalid.
- Order form URL contains `pcbPlaceOrder`.
- Success URL contains `pcbPlaceSuccess`.
- Order-check drawer: `.selectedParamsCompCheck` or visible `.el-drawer`.
- Price panel: `#rightcontent` or `.rightcontentBox`.
- Order-check button: `检查订单`.
- Submit from clean drawer: `确认并提交`.
- SMT confirmation modal after check: `请选择本单是否需要SMT贴片` -> `确定，不需要SMT`, then rerun `检查订单`.
- Success text: `订单提交成功，请等待审核`.

Block submission when the drawer is closed or contains `检测到您的订单还有`, `去填写`, `系统未检测到`, `余额不足`, or `充值`. Do not use the whole form body as submit evidence.

## Problems And Fixes

| Problem | Symptom | Method |
| --- | --- | --- |
| OSP blocked on small boards | `当前订单尺寸过小（任意边＜7cm），选择OSP工艺生产不能支持` | Pick a supported finish such as `选择无铅喷锡`; do not force OSP. |
| Paid compensation false positive | Unselected `元器件移植全额赔付` text remains in page DOM | Read only the visible order-check drawer and price panel; block only on selected paid fee. |
| Stencil remains unfilled | Drawer shows steel/stencil missing after no-SMT selection | Use actual label `是否开钢网 -> 不需要`. |
| Wrong `不需要` row clicked | Generic occurrence click hits SMT or another row | Click options by exact label/row, not by occurrence number. |
| Courier missing or changed | Drawer shows `快递方式 去填写` or wrong carrier | Select exact text `顺丰电商标快`. |
| Combined shipping conflict | SF rejects `并单发货` | Use `不同交期订单不一起发货`. |
| Ambiguous post-submit state | Form remains open briefly after click | Detect `pcbPlaceSuccess` and `订单提交成功，请等待审核`. |
| Board size missing | Drawer shows `板子尺寸 去填写` | Fill `input[placeholder='长']` and `input[placeholder='宽']` from the board config, in centimeters. |
| Wrong remembered material/layer | Drawer shows retained old material or 1-layer state | Reapply `板材类别`, `板子层数`, and `出货方式` every run by row label. |
| Customer code missing | Drawer shows `板上加标志 去填写` | Choose free customer code, then confirm the `加客编` modal. |
| Existing address blocks rerun | Address iframe or dialog intercepts earlier clicks | Accept the already-selected main-page address when contact/address text is present; close leftover address dialogs before refilling settings. |
| Legacy upload should be reused | User says the PCB is legacy/old and asks not to submit a new one | Use the existing uploaded row and its `pcbFileId`; do not upload a duplicate ZIP. |
| SMT modal blocks order check | `检查订单` opens `请选择本单是否需要SMT贴片` | Click `确定，不需要SMT`, then click `检查订单` again. |
| Confirm/shipping still missing | Drawer shows `确认订单方式 去填写` or `发货方式 去填写` | Select `确认订单方式 -> 手动确认订单` and `发货方式 -> 不同交期订单不一起发货` by label-local click. |
| Duplicate/stale JLC tabs | Guard sees old order state or unselected material labels | Prefer the tab with a visible clean order-check drawer for submit; prefer `pcbPlaceSuccess` for post-submit logs. |

## Script Methods

When adapting the AgenticApp tool, preserve these methods:

- `connect_page()`: score duplicate JLC tabs; prefer a visible clean order-check drawer for form work and `pcbPlaceSuccess` for post-submit logs.
- `selected_order_check_text()`: read selected values from the visible drawer.
- `visible_price_text()`: check the price panel for `品质赔付费`.
- `assert_clean_for_submit()`: central submit gate.
- `click_option_near_label()`: click row-local options such as SMT/stencil/edge polish.
- `fill_board_dimensions()`: writes board size in centimeters when JLC does not parse Gerber dimensions.
- `handle_customer_code_modal()`: confirms the `加客编` modal after selecting the free customer-code mark.
- `handle_smt_required_modal()`: confirms `确定，不需要SMT` when JLC asks again during order check.
- `select_courier()`: enforce the configured courier default.
- `record_order()` and `post_submit_log()`: private audit trail after check/submit.

## Global Flow

Known stable path:

1. Upload on `https://cart.jlcpcb.com/quote?spm=jlcpcb.Public.2006`.
2. Save the PCB item to cart.
3. Open `https://cart.jlcpcb.com/shopcart/cart/`.
4. Select `.data-choice-list .el-checkbox__inner`.
5. Confirm selected subtotal is nonzero.
6. Click `Secure Checkout`.
7. Fill China address from private config.
8. Choose `SF Express (Within Guangdong)` if available.
9. Click `Continue`.
10. Choose `Review Before Payment`.
11. Click `Submit Order`.

Success text: `Your order has been submitted.` Stop before payment.

## Desktop Assistant

Install locally from the official ZIP:

```bash
agentic_tools/jlcpcb_order_agent/scripts/install_assistant_local.sh \
  ~/Downloads/JLCPcAssit-linux-x64-5.0.69.zip
```

The app is unpacked under `~/.local/opt/jlc-assistant-5.0.69/`, wrapped by `~/.local/bin/jlc-assistant`, and stores its own private login/session in `~/.config/jlc-assistant`.

Use the stable launcher:

```bash
agentic_tools/jlcpcb_order_agent/scripts/launch_assistant_local.sh --restart
agentic_tools/jlcpcb_order_agent/scripts/launch_assistant_local.sh --status
```

Use the assistant only as a handoff unless separately automated. The assistant can show a cheaper price, but requires a desktop-app continuation and fresh CAM preview review. In remote Ubuntu desktops, the normal Electron sandbox may fail even with a setuid helper; the launcher starts the app in a separate `setsid` session, defaults to no-sandbox plus `--disable-gpu`, logs under `~/.cache/jlcpcb-order/assistant/`, and checks that the app stays alive. Keep extra Chromium flags empty unless debugging because the assistant can crash in its own command-line parser. If CDP is needed, set `JLCPCB_ASSISTANT_DEBUG_PORT=51369` and use raw page-level CDP; avoid Playwright browser-level attach for this Electron build.

## Database And Logs

Record every meaningful state transition privately:

```bash
python3 agentic_tools/jlcpcb_order_agent/scripts/jlc_order_cdp.py record-order \
  --status submitted_pending_review \
  --note "Submitted for JLC review; payment pending."
```

Keep database/log files mode `600`. Do not store OTP codes, cookies, screenshots with private fields, or payment credentials.
