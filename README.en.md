# hackintosh-b460i-mac26

Hackintosh workspace for a Colorful B460I + i5-10400 + RX 6800 build: migrated from macOS 13 to **macOS 26 Tahoe (26.6.2 / build 25G83)** and permanently fixed the "random black screen at boot" issue. [中文](README.md)

> Updated 2026-08-31: the black-screen issue is fixed. The machine now runs macOS Tahoe 26.6.2, boots via OpenCore **1.0.7**, with identical new EFI on both the internal disk ESP and the USB stick ESP. Verified across multiple reboots with a 100% success rate.

## Hardware

| Part | Model |
|---|---|
| Motherboard | Colorful B460I GAMING (mini-ITX) |
| CPU | Intel i5-10400 (Comet Lake) |
| GPU | AMD Radeon RX 6800 16GB (Navi 21) |
| WiFi/BT | Intel AX200 |
| OS | macOS Tahoe 26.6.2 (25G83) |
| Bootloader | OpenCore 1.0.7 |

## The Problem: Random Black Screen at Boot

**Symptoms**: verbose boot ran for about 35 seconds, then the screen went dark and the machine hung without rebooting; other boots succeeded. Reproducible by power-cycling, unrelated to warm/cold state.

**Diagnosis** (full record in [diagnostics/findings.md](diagnostics/findings.md)):

1. Mounted both ESPs (internal disk + USB stick), collected all OpenCore logs (13 + 7 files), a full NVRAM export, and 54 DiagnosticReports, then decoded all 4 kernel panics.
2. Every OpenCore log ended normally at `EXITBS:START` — the bootloader stage was fine; the failure was in the **kernel stage**.
3. Key correlation: **all 4 panics happened on boots via the internal disk's OLD EFI (OC 0.9.1), all 6 successful boots went through the USB stick's new EFI (OC 1.0.7)** — the failure tracked which EFI was used.
4. The decoded panic backtrace pinned the root cause:
   ```
   AMDRadeonX6000_AmdRadeonControllerNavi2::start
     → doGddr6LongTraining → doGPUPanic → panic
   ```
   i.e. **GDDR6 memory long-training failure on the RX 6800 (Navi 21)**. `debug=0x100` kept the panic on screen-less hold instead of rebooting — which is exactly what "black screen hang" looked like.

### Issues Found

| # | Issue | Status |
|---|---|---|
| 1 | Internal disk ESP still held the old Ventura EFI (OC 0.9.1 / Lilu 1.6.4 / WEG 1.6.4 / SecureBootModel=j185f) alongside the USB stick's new EFI; picking the wrong boot path triggered the GDDR6 training panic | **Root cause** |
| 2 | Several docs promised `ResizeAppleGpuBars=0`, but the key was absent from all three configs while BIOS Re-Size BAR was enabled — a known risk factor for Navi training panics | Fixed |
| 3 | The panic return variable `aapl,panic-info` was empty (macOS 26 now stores `AAPL,PanicInfo000K`); forensics scripts must read the new variable | Adapted |
| 4 | bluetoothd repeatedly crashed with EXC_GUARD (50+/day, Intel Bluetooth firmware handshake issue) | Non-fatal, watching |
| 5 | One shutdown_stall (forced power-off after a stuck shutdown) | One-off, unrelated |
| 6 | Mounting/writing the ESP requires admin auth; `sudo -n` is not viable, osascript GUI prompt required | Environment constraint |

## Solutions (all applied)

1. **Replaced the internal disk ESP with the OC 1.0.7 EFI**: `efi-new/tahoe-oc107/EFI` passed `ocvalidate` with zero issues, then `ditto`-deployed to disk0s1; `diff -rq` against the USB stick ESP reported identical. The old EFI backup was deleted at the owner's request. The "wrong boot path → black screen" hazard is gone.
2. **`NVRAM → Add → 7C43…9F82 → ResizeAppleGpuBars = 8`**: owner chose an 8GB BAR (matching the RX 6800's 16GB VRAM). Written to all three configs (repo / internal ESP / USB ESP) and added to the generator script `scripts/build_tahoe_config.py`; `ocvalidate 1.0.7` passes with zero issues. OC writes the value into NVRAM at next boot.
3. **Full observability retained**: `-v` verbose, `ApplePanic`, `Target=67` (OC logs land on the ESP root), `debug=0x100`, `agdpmod=pikera`, `-ibtcompatbeta revpatch=sbvmm` (Tahoe Bluetooth/OTA).

**Verification**: after the swap, every reboot went through the internal disk's new EFI with zero black screens or panics.

### If the GDDR6 training panic ever recurs (fallback plan)

- Disable Re-Size BAR in BIOS, or lock PCIe to Gen3 (hardware-level memory-training compatibility, residual probability unrelated to the EFI).
- The macOS 13-era EFI baseline remains in-repo: `efi-backup/original-20260830/`.

## Repository Layout

```
hackintosh-b460i-mac26/
├── README.md / README.en.md          # This file (ZH/EN)
├── AGENT_README.md                   # Onboarding guide for the handover USB's diagnostic agent
├── hardware/01-硬件清单.md            # Full hardware inventory
├── efi-backup/original-20260830/     # Read-only baseline of the macOS 13-era EFI (rollback)
├── efi-new/tahoe-oc107/EFI/          # ★ Live EFI source (= internal ESP = USB ESP)
│   └── companion/HeliPort-v1.5.0.dmg # AX200 WiFi utility
├── docs/                             # 02-08: config exports/diff/upgrade assessment/EFI notes/install guide/handover manual
├── diagnostics/                      # Black-screen forensics archive
│   ├── findings.md                   # ★ Three diagnostic rounds (root cause/changes/verification)
│   ├── opencore/                     # OC logs from both ESPs (13 from USB / 7 from internal)
│   ├── nvram/                        # Full NVRAM export
│   ├── panic/                        # 54 DiagnosticReports + 4 decoded panic logs
│   └── sysdiagnose/                  # Sysdiagnose archive
├── scripts/                          # Config analysis/patch/build scripts (all reproducible)
└── tools/                            # OC 0.9.1/1.0.7, ProperTree (binaries not committed)
```

## Related Docs (Chinese)

- [docs/06-Tahoe全新EFI说明.md](docs/06-Tahoe全新EFI说明.md) — new EFI components/parameters/risks
- [docs/07-全新安装macOS26完整步骤.md](docs/07-全新安装macOS26完整步骤.md) — full install walkthrough
- [diagnostics/findings.md](diagnostics/findings.md) — three-round diagnostic record
- [docs/08-外部诊断Agent交接手册.md](docs/08-外部诊断Agent交接手册.md) — forensics conventions and decision tree

## Git Conventions

Every change is committed; diagnostics are committed round by round (`b25ce79` forensics → `437a0d5` EFI swap → `bc4a6af` ResizeAppleGpuBars) so any stage can be revisited. Note: `diagnostics/` contains machine serial numbers and other private data — **keep this repository private**; scrub that directory before ever making it public.
