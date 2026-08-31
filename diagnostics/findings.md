# 诊断报告（外部 Agent 填写）

> 每轮诊断在文末追加一节，字段照抄模板。

```
## 诊断轮次 N（UTC 时间）
- 环境：（安装前验证 / S阶段卡点 / 已进系统）
- 现象：（一句话 + 触发操作）
- 已取证文件：（diagnostics/ 下新增文件清单）
- 初步结论：（引用日志行 / panic 符号）
- 已做改动：（kext/config 变更 + git commit 号）
- 建议/待办：
```

---

## 诊断轮次 1（2026-08-31 13:10 +0800，主会话取证）

- **环境**：已进系统 macOS 26.6.2 (25G83)，本次会话 12:40:40 经 U盘 OC 引导成功，GPU 正常（RX 6800 / Metal 3 / 16GB / WEG 1.7.0 生效）。

- **现象**：开机有概率黑屏卡死（verbose 跑约 35 秒后画面消失，机器不重启不死机但永远黑屏），有概率成功。强制断电重开可复现，成功率与"冷/热"无关、与**引导哪套 EFI 强相关**。

- **已取证文件**（本目录新增）：
  - `opencore/from-usb/`（13 份）、`opencore/from-internal/`（7 份）：两块 ESP 全部 OC 日志
  - `nvram/nvram-print.txt`、`nvram-print.xml`、`guid-AppleBoot.xml`、`guid-AppleRuntime.xml`
  - `panic/DiagnosticReports/`（54 份，含 4 份 Kernel panic）
  - `panic/decoded/`：4 份 panic 的 base64 解码全文
  - panic 回传盘 `aapl,panic-info` 为空（macOS 26 改存 `AAPL,PanicInfo000K`，见 nvram-print.txt 第 19 行）

- **根因结论（高置信）**：
  1. **"黑屏卡死"就是内核 panic**：`debug=0x100` 让 panic 不自动重启，而 panic 发生在 RX 6800 驱动初始化阶段（屏幕尚未点亮），所以表现为"黑屏挂住"。实锤 panic 栈（`panic/decoded/Kernel-2026-08-31-033105.panic.txt:7451`）：
     `AMDRadeonX6000_AmdRadeonControllerNavi2::start → doGddr6LongTraining → doGPUPanic → panic`
     即 **Navi 21 GDDR6 显存长训练失败**，开机 38 秒时触发。
  2. 今天共 4 次 panic 事件（03:24:20 / 03:31:25 / 03:44:43 / 12:33:11，uptime 全部 33–38 秒，同一时点）。四次 panic 会话的 boot-args 均为 `-v agdpmod=pikera keepsyms=1 debug=0x100`（**无** `-ibtcompatbeta`、`revpatch=sbvmm`），与**内置盘 ESP 的旧 config 完全一致**；而今天全部 6 次成功开机（02:46/03:51/04:29/04:38/04:40/12:40）boot-args 均含 `-ibtcompatbeta revpatch=sbvmm`，与 U盘 ESP 新 config 一致。
  3. 因此：**黑屏的开机 100% 走的是内置盘 disk0s1 上的旧 Ventura EFI（OC 0.9.1 老件：Lilu 1.6.4 / WEG 1.6.4 / SecureBootModel=j185f / 无 RestrictEvents）；成功的开机 100% 走 U盘 ESP 的 OC 1.0.7 新件。** docs/07 §7 要求的"把 U盘 EFI 回填内置盘"**并未执行**（内置 ESP 仍是老件，且挂载名仍为 NO NAME 带旧恢复分区）。
  4. **次要问题 A**：docs/02、05、06、08 均声称 config 有 `ResizeAppleGpuBars=0`（BIOS ResizeBAR 已开），但 USB ESP、内置 ESP、仓库 `efi-new/tahoe-oc107` 三份 config **均无此键**，`scripts/build_tahoe_config.py` 也没生成它——文档承诺从未落地。Ventura 时代即如此仍可用，但对 Navi GDDR6 训练是已知风险因子。
  5. **次要问题 B**：bluetoothd 今日崩溃 50+ 次（EXC_GUARD，Application Triggered Fault，见 `panic/DiagnosticReports/ExcUserFault_bluetoothd-*.ips`）——Intel 蓝牙固件与系统握手异常，用户态可自恢复，不致命，另行排查。
  6. 12:31 有一次 `shutdown_stall`（长会话正常关机卡住被强断），属偶发，与开机黑屏非同一问题。

- **已做改动**：无（本轮仅取证；config/EFI 未动）。

- **建议/待办**（按优先级）：
  1. **短期**：固定从 U盘 OC 引导（F11 → UEFI: U盘），当前 100% 成功率。
  2. **根治**：把 U盘 ESP 的 OC 1.0.7 新 EFI 回填内置盘 disk0s1（先备份旧 EFI 至 `efi-backup/`，`ocvalidate` 零问题 + git commit 后部署），消除"选错引导路径就黑屏"的隐患。
  3. 部署时顺带补上 `Misc→Boot→ResizeAppleGpuBars=0`（改 `build_tahoe_config.py` 后重建，ocvalidate 校验），兑现文档承诺。
  4. 若回填后仍偶发 `doGddr6LongTraining` panic：进 BIOS 关闭 ResizeBAR 或固定 PCIe Gen3 试之（硬件级显存训练兼容性，与 EFI 无关的残余概率）。
  5. 可选：清 NVRAM 残留 panic 变量 `AAPL,PanicInfo000K`（`sudo nvram -d AAPL,PanicInfo000K`）。
  6. 蓝牙崩溃问题单独开一轮诊断（先查 `IntelBluetoothFirmware 2.5.1 Tahoe fork` 与 Tahoe 26.6.2 的匹配性）。

---

## 第 2 轮（2026-08-31）：内置盘 EFI 已替换为 OC 1.0.7 新件

- **内置盘 ESP（disk0s1 → /Volumes/NO NAME）已完成回填**：旧 EFI 先备份至 `efi-backup/internal-old-20260831/`（62M），随后 `rm -rf` 旧 EFI、`ditto efi-new/tahoe-oc107/EFI` 部署新件；部署前 `ocvalidate 1.0.7` 零问题。
- **验证**：内置 ESP 与 U盘 ESP `diff -rq` 完全一致（exit 0）；与仓库差异仅为无害 AppleDouble `._*` 垃圾文件。
- **应机主要求，旧 EFI 备份 `efi-backup/internal-old-20260831/` 已删除**（仓库内仍留有更早的 `efi-backup/original-20260830/`）。至此"选错引导路径就黑屏"的隐患已消除：内置盘与 U盘均为同一套 OC 1.0.7 新 EFI。
- **ResizeAppleGpuBars 现状**：新 config（内置/U盘/仓库三处一致）**均无此键**。OC 对缺失键的处理是不改动 GPU BAR，即维持 BIOS 现状（Re-Size BAR = 开启）。docs 承诺的 `=0`（禁用）仍未落地，是否补写待机主确认。
- 待验证：多次重启，确认全部经内置盘新 EFI 引导且无 `doGddr6LongTraining` panic。
