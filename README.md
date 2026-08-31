# hackintosh-b460i-mac26

七彩虹 B460I + i5-10400 + RX 6800 黑苹果工作区：从 macOS 13 迁移到 **macOS 26 Tahoe (26.6.2 / 25G83)**，并根治了"开机有概率黑屏卡死"问题。[English](README.en.md)

> 2026-08-31 更新：黑屏问题已根治。现网运行 macOS Tahoe 26.6.2，引导 OpenCore **1.0.7**，内置盘与 U盘 ESP 均为同一套新 EFI，多次重启验证 100% 成功。

## 机器配置

| 部件 | 型号 |
|---|---|
| 主板 | 七彩虹 B460I GAMING (mini-ITX) |
| CPU | Intel i5-10400 (Comet Lake) |
| GPU | AMD Radeon RX 6800 16GB (Navi 21) |
| WiFi/BT | Intel AX200 |
| 系统 | macOS Tahoe 26.6.2 (25G83) |
| 引导 | OpenCore 1.0.7 |

## 问题：开机有概率黑屏卡死

**现象**：开机 verbose 跑约 35 秒后画面消失，机器挂住不重启；有时又能正常进系统。断电重开可复现，与冷热无关。

**诊断过程**（详见 [diagnostics/findings.md](diagnostics/findings.md)）：

1. 挂载内置盘与 U盘两块 ESP，采集全部 OpenCore 日志（13 + 7 份）、NVRAM 全量导出、54 份 DiagnosticReports，并把 4 份内核 panic 解码全文。
2. 发现所有 OC 日志都正常止于 `EXITBS:START`——OC 引导阶段没问题，故障在**内核阶段**。
3. 关键证据链：**4 次 panic 全部发生在走内置盘旧 EFI（OC 0.9.1）的开机，6 次成功全部走 U盘新 EFI（OC 1.0.7）**——故障与引导哪套 EFI 强相关。
4. 解码 panic 回溯实锤根因：
   ```
   AMDRadeonX6000_AmdRadeonControllerNavi2::start
     → doGddr6LongTraining → doGPUPanic → panic
   ```
   即 **RX 6800 (Navi 21) GDDR6 显存长训练失败**。`debug=0x100` 让 panic 停住不重启，而此时屏幕尚未点亮，所以表现为"黑屏挂死"。

### 发现的问题清单

| # | 问题 | 定性 |
|---|---|---|
| 1 | 内置盘 ESP 仍是旧 Ventura EFI（OC 0.9.1 / Lilu 1.6.4 / WEG 1.6.4 / SecureBootModel=j185f），与 U盘新 EFI 并存，选错引导路径即触发 GDDR6 训练 panic | **根因** |
| 2 | 多份文档承诺 `ResizeAppleGpuBars=0`，但实际三份 config 均无此键，而 BIOS Re-Size BAR 开启——Navi 显卡训练 panic 的已知风险因子 | 已修复 |
| 3 | panic 回传变量 `aapl,panic-info` 为空（macOS 26 改存 `AAPL,PanicInfo000K`），取证脚本需按新变量取 | 已适配 |
| 4 | bluetoothd 反复 EXC_GUARD 崩溃（50+ 次/日，Intel 蓝牙固件握手异常） | 非致命，观察中 |
| 5 | 一次 shutdown_stall（关机卡住被强断） | 偶发，与黑屏无关 |
| 6 | 挂载/写 ESP 需管理员授权，`sudo -n` 不可行，需 osascript GUI 授权 | 环境约束 |

## 解决方案（已全部实施）

1. **内置盘 ESP 回填 OC 1.0.7 新 EFI**：`efi-new/tahoe-oc107/EFI` 经 ocvalidate 零问题后 `ditto` 部署到 disk0s1，与 U盘 ESP `diff -rq` 完全一致；旧 EFI 备份经机主确认后删除。"选错引导路径就黑屏"的隐患随之消除。
2. **`NVRAM → Add → 7C43…9F82 → ResizeAppleGpuBars = 8`**：机主选定 8GB BAR（匹配 RX 6800 的 16G 显存），已写入仓库/内置盘/U盘三处 config 并同步进生成脚本 `scripts/build_tahoe_config.py`，`ocvalidate 1.0.7` 零问题。该值在重启时由 OC 写入 NVRAM 生效。
3. **保留完整可观测性**：`-v` 跑码、`ApplePanic`、`Target=67`（OC 日志落 ESP 根）、`debug=0x100`、`agdpmod=pikera`、`-ibtcompatbeta revpatch=sbvmm`（Tahoe 蓝牙/OTA）。

**验证结果**：替换后多次重启，全部从内置盘新 EFI 引导，无一次黑屏/panic。

### 若复发 GDDR6 训练 panic（回退预案）

- 进 BIOS 关闭 Re-Size BAR，或将 PCIe 锁 Gen3（硬件级显存训练兼容性，与 EFI 无关的残余概率）。
- 引导基线仍在仓库：`efi-backup/original-20260830/`（macOS 13 时代完整 EFI）。

## 目录结构

```
hackintosh-b460i-mac26/
├── README.md / README.en.md          # 本文件（中/英）
├── AGENT_README.md                   # 交接 U盘用：外部诊断 Agent 上手指南
├── hardware/01-硬件清单.md            # 硬件型号/ID/驱动方式总表
├── efi-backup/original-20260830/     # macOS13 时代 EFI 完整只读基线（回滚用）
├── efi-new/tahoe-oc107/EFI/          # ★ 现役 EFI 源（= 内置盘 ESP = U盘 ESP）
│   └── companion/HeliPort-v1.5.0.dmg # AX200 WiFi 连接工具
├── docs/                             # 02-08：config 导出/diff/升级评估/EFI 说明/装机步骤/交接手册
├── diagnostics/                      # 黑屏取证档案
│   ├── findings.md                   # ★ 三轮诊断记录（根因/改动/验证）
│   ├── opencore/                     # 双 ESP 的 OC 日志（from-usb 13 份 / from-internal 7 份）
│   ├── nvram/                        # NVRAM 全量导出
│   ├── panic/                        # 54 份 DiagnosticReports + 4 份 panic 解码全文
│   └── sysdiagnose/                  # 系统诊断包
├── scripts/                          # config 分析/补丁/构建脚本（全部可复现）
└── tools/                            # OC 0.9.1/1.0.7、ProperTree（二进制不入库）
```

## 相关文档

- [docs/06-Tahoe全新EFI说明.md](docs/06-Tahoe全新EFI说明.md) — 新 EFI 组件/参数/风险
- [docs/07-全新安装macOS26完整步骤.md](docs/07-全新安装macOS26完整步骤.md) — 装机全流程
- [diagnostics/findings.md](diagnostics/findings.md) — 黑屏三轮诊断记录
- [docs/08-外部诊断Agent交接手册.md](docs/08-外部诊断Agent交接手册.md) — 取证规范与判定树

## Git 约定

改动即 commit（诊断分轮提交：`8aa74d2` 取证 → `84d0394` EFI 回填 → `75cbcbe` ResizeAppleGpuBars），可逐阶段回溯。仓库内 config 的 PlatformInfo（序列号/MLB/UUID/ROM）已替换为占位符，克隆使用前请用 GenSMBIOS 等工具生成自己的标识。
