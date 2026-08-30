# 08 · 外部诊断 Agent 交接手册（U 盘内容 · 跑码取证 · 修复规程）

> **致外部诊断 Agent**：本手册与一个安装 U 盘一并交接给你。目标是这台七彩虹 B460I 黑苹果的 **macOS 26 (Tahoe) 全新安装**：请按 `docs/07` 执行安装，若引导/安装跑码卡住，按本手册 §6 判定树定位、§7 取证、§9 修复。你手上这个 U 盘 = 安装介质 + 本仓库完整副本 + 日志回传区，离线自足。
>
> **红线（必读）**：
> 1. **抹盘是破坏性操作**：系统盘 disk0 的 APFS 容器含 824.7GB 用户数据卷 `macos - 数据`。**抹盘前必须获得机主本人明确确认**，且只允许抹 1TB 的 disk0，**严禁触碰 12TB 的 disk2**（游戏/办公/文档代码/MAC 卷）。
> 2. 所有对 EFI/config 的修改**先入库（git commit）再部署**，每步留下可回滚点。
> 3. 取证优先于修复：先按 §7 拿到日志/panic 数据，再动手改配置。

---

## 1. U 盘内容地图（250GB，HFS+ 卷名 `Install macOS Tahoe`）

| 路径 | 内容 |
|---|---|
| `/（卷根）` | macOS Tahoe 26.6.2 (build 25G83) 全新安装器（createinstallmedia 写入，**勿删改安装文件**） |
| `/AGENT_README.md` | 给你的入口指南（本手册的速查版） |
| `/hackintosh-b460i-mac26/` | **本仓库完整副本（含 .git 全部提交历史）**：docs 01–08、hardware、efi-new、efi-backup、scripts、tools（OC 0.9.1/1.0.7 + ProperTree）、upstream |
| `/hackintosh-b460i-mac26/efi-new/tahoe-oc107/EFI/` | ★ Tahoe 新 EFI 源（OC 1.0.7，与 U 盘 ESP 内内容同源） |
| `/hackintosh-b460i-mac26/efi-new/companion/HeliPort-v1.5.0.dmg` | AX200 WiFi 连接工具（装完系统安装） |
| `/hackintosh-b460i-mac26/efi-backup/original-20260830/` | 现网 13 的原版 EFI 完整基线（回滚用，含旧恢复镜像） |
| `U盘 ESP（EFI 分区，≈200MB）` | 已部署的 Tahoe OC 1.0.7 EFI（引导实际使用的副本） |
| `/diagnostics/` | **你的日志回传区**（结构见 §8），opencore / panic / sysdiagnose / photos / findings.md |

> HeliPort 也复制了一份在卷根附近随 U 盘走；安装卷在安装完成后仍可读写，取证文件直接写进 `/diagnostics/`。

## 2. 目标机器档案

| 项 | 值 |
|---|---|
| 主板 | 七彩虹 CVN B460I GAMING FROZEN V20（ITX），BIOS 1007，**ResizeBAR 已开**（故 config 有 `ResizeAppleGpuBars=0`） |
| CPU | i5-10400（Comet Lake-S，6C12T）+ UHD630 **headless**（`0x3E920003`，不接屏） |
| 独显 | **RX 6800 16GB**（1002:73BF，Navi 21）原生免驱，`agdpmod=pikera`，显示器接此卡（GX321UR 6K HiDPI@100Hz DP） |
| 系统盘 | 白泽 1TB NVMe = **disk0**（见 §5 红线） |
| 数据盘 | Synology 12TB HDD = disk2（3×NTFS + 1×APFS"MAC"，**不动**） |
| 网卡 | 有线 RTL8111（en1）；无线 **AX200**（en0，itlwm 2.3.0 + HeliPort） |
| 蓝牙 | AX200 集成（USB 8087:0029）：IntelBluetoothFirmware **2.5.1 Tahoe fork** + IntelBTPatcher + BlueToolFixup + `-ibtcompatbeta` |
| 声卡 | ALC662（layout-id=7）；**Tahoe 板载模拟音频已知受限**（docs/06 §5），DP/HDMI 数字音频正常 |
| USB | USBPorts.kext 定制映射，XhciPortLimit=False |
| SMBIOS | iMac20,1（三码沿用现网） |
| SIP | `03000000`（部分关闭） |

## 3. 两套 EFI 与交接时状态

| | 现网（内置盘 disk0s1 ESP，8.6GB） | U 盘 ESP（本次交接） |
|---|---|---|
| 系统 | macOS 13.7.8 | macOS Tahoe 26.6.2 安装器 |
| OpenCore | 0.9.1（2023-05）+ verbose 调试已开 | **1.0.7（Tahoe 全新件，18 kext 最新版）** |
| config | `config.plist.bak-before-verbose` 可回滚 | ocvalidate 1.0.7 零问题 |
| 用途 | 现网 13 / 回滚基线 | 引导安装 Tahoe；安装成功后回填内置盘 |

Tahoe 新 EFI 关键项：SecureBootModel=**Disabled**；10 个本机 SSDT（AWAC/DMAC/EC/GPRW/MCHC/MEM2/PLUG/PMCR/RHUB/SBUS）原样迁移；USBPorts/CPUFriendDataProvider/显卡温度 kext/iMac20,1 三码/Canopy 主题均迁移；RestrictEvents 1.1.6 + `revpatch=sbvmm`（保 OTA）。

## 4. 调试开关与日志落点（新 EFI 已全部开启）

| 开关 | 值 | 效果 / 日志落点 |
|---|---|---|
| `-v` | boot-args | 内核 verbose 跑码直接上屏（无苹果 logo） |
| `debug=0x100` | boot-args | **panic 不自动重启**，panic 屏常驻供拍照 |
| `keepsyms=1` | boot-args | panic/跑码保留符号（可读函数名） |
| `ApplePanic` | config=true | panic 全文写入 NVRAM `aapl,panic-info`，重启后仍可取：`nvram -x aapl,panic-info > panic.xml` |
| `Target=67` | config | 0x43 = 开启 + 控制台 + **文件**：OpenCore 日志写 **ESP 根** `opencore-YYYY-MM-DD-hhmmss.txt` |
| `-ibtcompatbeta` | boot-args | Intel 蓝牙 Tahoe fork 兼容标记 |
| `revpatch=sbvmm` | boot-args | OTA 放行（RestrictEvents） |
| `agdpmod=pikera` | boot-args | Navi GPU (RX6800) board-id 补丁 |

## 5. 安装操作规程（全文见 `docs/07`，此处为执行摘要）

1. F11 → **UEFI: U盘** → OC 选择器 → **先选现网 13 验证 U 盘 OC 引导链**（通过前不得抹盘）。
2. 选 `Install macOS Tahoe` 进安装器 → 磁盘工具 → 显示所有设备 → **只选 1TB disk0** → 抹成 GUID + APFS（`Macintosh HD`）→ **抹盘前向机主确认**（红线）。
3. 安装 → 重启若干次，每次都从 U 盘 OC 引导：第二阶段起选内置盘的 **`macOS Installer`**（选错 U 盘安装器会重头装），最后条目变 `Macintosh HD`。
4. 设置助理：本地账户先行（可离线）；WiFi 装 HeliPort（卷根有 dmg）或有线直插。
5. 稳定后按 docs/07 §7 把 U 盘 ESP 的 EFI 回填 disk0s1。

## 6. 跑码卡点判定树

| 症状 | 阶段 | 查什么 / 动什么 |
|---|---|---|
| 主板菜单看不到 U 盘 | S0 | BIOS：Above 4G 开 / CSM 关 / Secure Boot 关；重挂 U 盘 ESP 检查 `EFI/OC/OpenCore.efi` 与 `config.plist` 是否完整 |
| OC 选择器不出现 | S1 | 屏幕有无 OC 主题；从 13 系统挂 U 盘 ESP，`ocvalidate` 校验 config；确认 `Misc/Boot/HideAuxiliary` 与 `PickerMode` |
| 选中安装器后黑屏无跑码 | S2 | 抓 ESP 根 `opencore-*.txt` 最后 100 行：看最后加载的 kext/driver/SSDT；对照 `docs/05` 核对 config 全量 |
| 卡 `EXITBS:START`（无 END） | S3 | Booter/ACPI 问题：确认 10 个 SSDT 全部加载（opencore 日志有 ACPI 表清单）；查 Quirks（AvoidRuntimeDefrag/DevirtualiseMmio/EnableWriteUnprotector 等） |
| 卡 `gIOScreenLockState`/`IOConsoleDrivers` 或 WEG/AMD panic | S4 | **docs/06 §6 预案**：WEG 1.7.0 在 Tahoe 的 AMD connector 补丁风险。确认 panic 指向 WhateverGreen 后才移除 WEG + 改 Kernel→Patch 手工 AppleGraphicsDevicePolicy 补丁（pikeralpha 方案）；注意 UHD630 headless 依赖 WEG，移除后核显加速丢失 |
| `Still waiting for root device` | S5 | 换 U 盘到后置 USB2.0 口重试；查 USBPorts 映射与 XhciPortLimit=False；NVMeFix 是否加载（白泽 NVMe） |
| panic 屏（debug=0x100 常驻） | S6 | 拍照（photos/）+ `nvram -x aapl,panic-info`（panic/）+ opencore 日志；按 §7 完整取证后对照 §9 |
| 安装进度长期卡住 | S7 | "剩余不到 1 分钟"卡 30–60 分钟属正常；真卡死进安装器终端看 `/var/log/install.log` 尾部 |
| 进系统后某硬件异常 | S8 | §7 系统内取证 + docs/06 §5（音频）/§9（风险点）逐项核对 |

## 7. 取证命令速查（在 macOS/安装器/Recovery 终端均可执行）

```bash
# 环境与版本
sw_vers; uname -a; system_profiler SPHardwareDataType SPDisplaysDataType SPAudioDataType SPMemoryDataType SPNVMeDataType

# OpenCore 日志（ESP 根，Target=67 写入）
diskutil list                                   # 找 EFI 分区
diskutil mount diskXsY                          # 挂 ESP（装好的系统内需 sudo）
cp /Volumes/EFI/opencore-*.txt /Volumes/Install\ macOS\ Tahoe/diagnostics/opencore/

# Kernel panic（ApplePanic 落 NVRAM，重启不丢）
nvram -x aapl,panic-info > /Volumes/Install\ macOS\ Tahoe/diagnostics/panic/panic-info.xml
# 已进系统后还可收集：
cp -a /Library/Logs/DiagnosticReports /Volumes/Install\ macOS\ Tahoe/diagnostics/panic/ 2>/dev/null

# 系统日志与硬件树（已进系统）
log show --last 30m --style syslog > /Volumes/Install\ macOS\ Tahoe/diagnostics/sysdiagnose/systemlog.txt
sudo sysdiagnose -f /Volumes/Install\ macOS\ Tahoe/diagnostics/sysdiagnose/   # 全量打包，约数分钟
ioreg -l -w 0 > /Volumes/Install\ macOS\ Tahoe/diagnostics/sysdiagnose/ioreg.txt
kextstat > /Volumes/Install\ macOS\ Tahoe/diagnostics/sysdiagnose/kextstat.txt
pmset -g log > /Volumes/Install\ macOS\ Tahoe/diagnostics/sysdiagnose/pmset.log

# GPU 加速判定：system_profiler SPDisplaysDataType 里 Metal=Supported、显存 16384MB 即 WEG 生效

# 屏幕拍照（跑码/panic 屏无法复制时）：手机拍 → 存 diagnostics/photos/，命名 S阶段_时间.jpg
```

安装器内开终端：安装器菜单栏 **实用工具 → 终端**（nvram / diskutil / cp 可用）。

## 8. 日志回传规范

写回 U 盘 `/diagnostics/`，目录固定：

```
diagnostics/
├── opencore/     # opencore-*.txt（保留原始文件名）
├── panic/        # panic-info.xml、DiagnosticReports 拷贝
├── sysdiagnose/  # sysdiagnose 包、log show、ioreg、kextstat、pmset
├── photos/       # 跑码/panic 屏照片，命名 <阶段>_<时间>.jpg
└── findings.md   # 诊断报告（模板见下）
```

`findings.md` 模板（每轮诊断追加一节）：

```markdown
## 诊断轮次 N（UTC 时间）
- 环境：（安装前验证 / S阶段卡点 / 已进系统）
- 现象：（一句话 + 触发操作）
- 已取证文件：（列出 diagnostics/ 下新增文件）
- 初步结论：（引用日志行/panic 符号）
- 已做改动：（kext/config 变更，附 git commit）
- 建议/待办：
```

> 诊断完成后把 `/diagnostics/` 拷回本仓库 `docs/forensics/`（由主会话归档入库）。

## 9. 修复工具与手段（都在 U 盘里）

- **改 plist**：`tools/ProperTree/ProperTree.py`（`python3 ProperTree.py`，图形界面）；改完必须校验。
- **校验**：`tools/oc-1.0.7/Utilities/ocvalidate/ocvalidate <config.plist>`（二进制直接运行），**零问题才允许部署**。
- **重建 EFI**（改了 kext/大改 config 时首选）：仓库自带可复现脚本
  `bash scripts/build_new_efi.sh`（重建 `efi-new/tahoe-oc107`）+ `python3 scripts/build_tahoe_config.py`（生成 1.0.7 schema config）。需联网拉取最新组件。
- **WEG 风险预案**：见 §6 S4 与 docs/06 §6（最后手段：移除 WEG + 手工 AGDP 补丁，核显加速会丢）。
- **音频**：Tahoe 模拟音频受限（ALC662 layout-id=7 可能无声），方案清单在 docs/06 §5（VoodooHDA / 根补丁二选一）；数字音频不受影响。
- **WiFi**：itlwm 2.3.0 已随 EFI 加载，连接必须 HeliPort（无 HeliPort 无法选网）；AirportItlwm 是备选路线（要换 kext + 系统根补丁，不推荐首选）。
- **OTA**：RestrictEvents + revpatch=sbvmm + SecureBootModel=Disabled 已配置，勿动。

## 10. 应急与回滚

| 场景 | 动作 |
|---|---|
| U 盘 OC 起不来 / 改坏 ESP | 从 13 系统重拷 `efi-new/tahoe-oc107/EFI` 到 U 盘 ESP |
| Tahoe 装失败想回 13 | 现网 13 未抹前：拔 U 盘从内置 OC 进 13；已抹：需重做 Ventura 安装 U 盘 + 回写 `efi-backup/original-20260830` 的 EFI |
| 现网 13 引导异常（未抹盘阶段） | `efi-work/verbose-20260830/` 有部署副本；`config.plist.bak-before-verbose` 是最后一版正常 config |
| 全部失败 | 13 可正常引导使用，本机无不可逆损失（**前提：抹盘前的数据已按机主意愿处置**） |

## 11. 文档索引

| 文档 | 内容 |
|---|---|
| `docs/04-macOS26升级评估与排查方案.md` | 黑屏根因分析、26 兼容性矩阵、取证方法 |
| `docs/05-tahoe新config全量.txt` | 新 config 全量关键项（对照基准） |
| `docs/06-Tahoe全新EFI说明.md` | 组件清单、WiFi/音频/OTA、WEG 风险、风险点 |
| `docs/07-全新安装macOS26完整步骤.md` | 安装全流程（本手册 §5 的全文） |
| `hardware/01-硬件清单.md` | 硬件/kext/BIOS 总表 |
| `.git` 历史 | 全部变更逐阶段可回溯（备份→分析→构建→部署） |
