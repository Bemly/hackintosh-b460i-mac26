# 06 · macOS 26 Tahoe 全新 EFI 说明（OC 1.0.7）

> 产物目录：`efi-new/tahoe-oc107/EFI/`
> 配套软件：`efi-new/companion/HeliPort-v1.5.0.dmg`
> 生成脚本：`scripts/build_new_efi.sh`（组装文件）+ `scripts/build_tahoe_config.py`（生成 config）
> 校验：`tools/oc-1.0.7/Utilities/ocvalidate/ocvalidate config.plist` → **No issues found**；`plutil -lint` → OK
> 目标：只服务 macOS 26 Tahoe，不再兼顾 macOS 13。**当前仅入库，未部署到 EFI 分区。**

---

## 1. 组件清单（18 kext / 5 driver / 2 tool / 10 SSDT）

### Kexts（Kernel/Add 按此顺序加载，Lilu 必须第 0 位）

| # | Kext | 版本 | 作用 | 来源 |
|---|------|------|------|------|
| 0 | Lilu | 1.7.2 | 补丁框架，一切插件的前提 | Acidanthera 最新 release |
| 1 | VirtualSMC | 1.3.7 | SMC 仿真（必需） | Acidanthera |
| 2 | SMCProcessor | 1.3.7 | CPU 温度 | 同上 |
| 3 | SMCSuperIO | 1.3.7 | 风扇读数 | 同上 |
| 4 | WhateverGreen | 1.7.0 | 核显 headless / 独显补丁 | Acidanthera（Tahoe 风险见 §6） |
| 5 | AppleALC | 1.9.7 | ALC662 layout-id 7（**Tahoe 模拟音频限制见 §5**） | Acidanthera |
| 6 | CPUFriend | 1.3.0 | CPU 变频 | Acidanthera |
| 7 | CPUFriendDataProvider | 本机 1.0.0 | 本机变频数据（**沿用旧 EFI，不可换通用版**） | 旧 EFI |
| 8 | NVMeFix | 1.1.3 | NVMe 电源/修正 | Acidanthera |
| 9 | **itlwm** | 2.3.0 | Intel AX200 WiFi 驱动（配 HeliPort，见 §4） | OpenIntelWireless |
| 10 | IntelBluetoothFirmware | **2.5.1** | AX200 蓝牙固件（Tahoe 修复 fork） | lshbluesky fork |
| 11 | IntelBTPatcher | **2.5.1** | 蓝牙补丁（Tahoe 修复 fork） | lshbluesky fork |
| 12 | BlueToolFixup | 2.7.2 | Monterey 起蓝牙栈修复（取自 BrcmPatchRAM） | Acidanthera |
| 13 | RestrictEvents | 1.1.6 | 让 Tahoe 能收到 OTA（配 `revpatch=sbvmm`，见 §7） | Acidanthera |
| 14 | RealtekRTL8111 | 3.0.0 | RTL8111 有线（已加 Tahoe/AppleVTD 支持） | Mieze |
| 15 | RadeonSensor | 0.3.3 | RX6800 温度（**无新版，沿用旧 EFI**） | 旧 EFI |
| 16 | SMCRadeonGPU | 0.3.3 | RX6800 传感器（沿用旧 EFI） | 旧 EFI |
| 17 | USBPorts | 本机 1.0 | 本机 USB 端口映射（**定制件，沿用，不可换**） | 旧 EFI |

**明确移除**：`XHCI-unsupported.kext`（Comet Lake PCH 控制器 8086:a3a3 本就被 macOS 原生支持，无需该补丁；官方亦停更于 0.9.2）；`IntelBluetoothInjector.kext`（Monterey 起必须删除，否则蓝牙异常）；`AppleALCU.kext` 及 VirtualSMC 全家桶里的 Dell/Battery/LightSensor（本机不需要）。

### Drivers（UEFI/Drivers）
OpenRuntime（必需）、OpenCanopy（图形菜单）、**OpenHfsPlus**（官方开源 HFS，替代旧的闭源 HfsPlus.efi）、ResetNvramEntry（菜单重置 NVRAM）、CrScreenshotDxe（开机截图）。

### Tools（Misc/Tools，开机按空格在辅助菜单显示）
OpenShell.efi（UEFI Shell 排障）、CsrUtil.efi（SIP 切换）。

### ACPI
原样沿用旧 EFI 的 10 个 SSDT：AWAC / DMAC / EC / GPRW / MCHC / MEM2 / PLUG / PMCR / RHUB / SBUS。

### Resources
沿用旧 EFI 的全套图形主题（Blackosx BsxOc1 + Acidanthera 字体/图标/音频），跨 OC 版本兼容。

---

## 2. 从旧 EFI 原样迁移的本机定制（勿改）

- **SMBIOS 三码**：iMac20,1 + 原序列号/MLB/UUID/ROM（Tahoe 支持机型清单含 iMac2019/2020，iMacPro1,1 在 Tahoe 已不支持，故必须保持 iMac20,1）。
- **核显 UHD630 headless**：`PciRoot(0x0)/Pci(0x2,0x0)` → `AAPL,ig-platform-id=0300923e`、`device-id=c89b0000`（核显不接显示器，只做硬件加速）。
- **独显 RX6800**：原生免驱，接显示器；`agdpmod=pikera` 保留（Navi 关闭 board-id 检查，防黑屏）。
- **声卡 ALC662**：`PciRoot(0x0)/Pci(0x1F,0x3)` → `layout-id=7`。
- Booter/Kernel/UEFI 全部 Quirks 沿用旧值（AvoidRuntimeDefrag、DevirtualiseMmio、ResizeAppleGpuBars=0、DisableIoMapper、SetApfsTrimTimeout=-1 等），并按 1.0.7 schema 补齐了新增键（ClearTaskSwitchBit/FixupAppleEfiImages/DisableIoMapperMapping/GopBurstMode/InitialMode/PciIo/ResizeUsePciRbIo/ShimRetainProtocol 等，均取安全默认值）。
- 菜单外观：External 图形菜单、Blackosx 主题、Timeout=3、UIScale=02、中文 prev-lang:kbd。

## 3. 用户点名的调试设置（已落实）

- `boot-args = -v -ibtcompatbeta revpatch=sbvmm agdpmod=pikera keepsyms=1 debug=0x100`
  - `-v`：**开机跑码不跑 logo**，卡在哪一行直接可见；
  - `keepsyms=1 debug=0x100`：panic 保留符号、重启前停留；
  - `-ibtcompatbeta`：Tahoe 启用 Intel 蓝牙的必需参数（Dortania Tahoe 指南）；
  - `revpatch=sbvmm`：配合 RestrictEvents 让 OTA 可用（§7）；
  - `agdpmod=pikera`：RX6800 防黑屏。
- `Misc/Debug`：AppleDebug=true、**ApplePanic=true**、**Target=67**（屏幕显示 + 写日志文件到 EFI）、DisableWatchDog=true。
- `Misc/Security`：**SecureBootModel=Disabled**（Tahoe 升级期最稳，且 OTA 要求；与上游 4.0.0 一致）、Vault=Optional、ScanPolicy=0。
- `csr-active-config=03000000`（部分关闭 SIP，itlwm/VoodooHDA 等需要）。

---

## 4. WiFi（AX200）为什么"没驱动起来"与最终方案

**诊断结论**：旧 EFI 里 itlwm 2.1.0 其实已成功匹配 AX200（ioreg 可见、en0 已生成、MAC 正常），但纯 itlwm 只创建一个"以太网式"接口，**连接热点必须靠 HeliPort.app 这个菜单栏管理工具**；本机 `/Applications` 里没有 HeliPort，也没有其进程 —— 这就是"WiFi 没驱动起来"的真因：驱动在，缺连接工具。

**方案（纯 itlwm 路线，不用根补丁）**：
1. EFI 内已放最新 **itlwm 2.3.0**；
2. 进系统后安装 **HeliPort**（`efi-new/companion/HeliPort-v1.5.0.dmg`，拖到"应用程序"），从菜单栏 HeliPort 图标选 SSID、输密码连接；
3. 本次已在当前 macOS 13 上先行安装并启动 HeliPort 验证：进程正常、与 itlwm 的 `com.zxystd.itlwm` 服务通道连通、en0 UP/RUNNING，选网即可用。

**为什么不用 AirportItlwm**：它能让 WiFi 出现在系统原生菜单，但在 Sequoia/Tahoe 必须配合 OCLP-Mod 根补丁（IOSkywalkFamily 替换 + IOName 伪装 + AMFIPass + 更激进的 SIP 03080000），侵入性和维护成本高；纯 itlwm+HeliPort 不动根卷，升级系统后不易掉。代价：Intel WiFi 本就没有隔空投送/接力（AWDL），HeliPort 是独立菜单而非系统 WiFi 图标。

> 备注：itlwm 公开 release 停在 2.3.0（2024-06），纯 itlwm 不依赖系统 WiFi 私有框架，跨版本能力强；若 Tahoe 下出现异常，再换 OpenIntelWireless master 的 CI 构建。

## 5. ⚠️ 板载模拟音频在 Tahoe 的已知限制（重要预期管理）

macOS 26 **删除了 AppleHDA.kext，导致 AppleALC 失效**（Dortania Tahoe 指南明确）。也就是说：升级后，主板 3.5mm 耳机孔/后置音频口默认会**没有声音**。

- **不受影响**：走 RX6800 的 DP/HDMI 音频（显示器喇叭/耳机）、USB 声卡/蓝牙耳机 —— 这些是数字音频，照常工作。
- **要恢复 3.5mm 模拟音频，二选一**：
  1. **OCLP-Mod 根补丁重新注入 AppleHDA**（音质最好，但要改只读根卷，每次系统小更新后要重新补丁，与黑苹果 OCLP 同样的弊端）；
  2. **VoodooHDA**（不依赖 AppleHDA；Tahoe 用 chris1111/VoodooHDA-Tahoe 构建的 pkg 安装到 `/Library/Extensions`，保持 csr-active-config=03000000，系统设置里允许加载；音质略逊 AppleALC，偶有底噪）。
- 新 EFI **保留 AppleALC**（数字输出/日后根补丁仍需要，且无副作用），但不预装 VoodooHDA（是否牺牲音质由你决定）。需要时按上面任一方案操作即可。

## 6. ⚠️ WhateverGreen 在 Tahoe 的潜在 panic 与备用手段

Dortania 指出 WEG 在 macOS 26 上对 **AMD 显卡的接口（connector）补丁存在问题**，极少数情况会在 WEG/AMD 相关 kext 处内核 panic，且暂无完美 workaround，只能整个移除 WEG；若移除后又需要 `agdpmod=pikera`，则改为在 `Kernel→Patch` 手工打 AppleGraphicsDevicePolicy 的 board-id→none 二进制补丁（参考 pikeralpha：https://pikeralpha.wordpress.com/2015/11/23/patching-applegraphicsdevicepolicy-kext/ ）。

本机策略：**先用 WEG 1.7.0（2026-02 发布，比该指南更新）+ pikera 正常引导**。因为 UHD630 headless 也依赖 WEG，贸然移除会丢核显加速。只有当 verbose 跑码明确停在 WhateverGreen/AMD GPU 相关 panic 时，才按本节移除 WEG 并改手工补丁（届时再出一版 config）。

## 7. OTA 系统更新

macOS 14.4 起，黑苹果要在系统内收到 OTA 必须：RestrictEvents.kext + `revpatch=sbvmm`，且 SecureBootModel=Disabled —— 三者均已配置。升级 Tahoe 后可直接在"系统设置→通用→软件更新"收后续增量。

## 8. 上 Tahoe 的操作步骤（建议先 U 盘验证，不动现网）

1. 找一个 U 盘（GUID + FAT32），把 `efi-new/tahoe-oc107/EFI` 整个拷到 U 盘 EFI 分区根目录；
2. 开机 F11 选 U 盘启动，verbose 跑码验证能否进现有 macOS 13（**先验证新 OC 能引导旧系统**，此时 itlwm/HeliPort 照常）；
3. 用系统内"软件更新"或制作 Tahoe 安装 U 盘，在新 OC 下安装/升级 macOS 26；
4. 跑码若卡住：拍照最后一屏（Target=67 同时会把日志写进 EFI/OC 或 ESP 根），对照 §5/§6 排查；
5. Tahoe 稳定运行后，再把该 EFI 覆盖到硬盘 ESP（disk0s1）；覆盖前现网备份已在 `efi-backup/original-20260830/`，可随时回滚。

## 9. 尚未经真机验证的风险点

- itlwm 2.3.0 / IntelBluetooth 2.5.1 fork 在 Tahoe 26.5+ 的稳定性来自社区报告（AX200/AX210 系列有成功案例），本机未实机升 26；
- 模拟音频需按 §5 二次处理；
- WEG 1.7.0 在本机 RX6800 上是否触发 §6 的问题需 verbose 实测；
- Tahoe 是最后一代支持 Intel 黑苹果的系统，后续大版本不再有。

---

### 附：一键重新生成（改了 kext 或配置后）
```bash
cd ~/hackintosh-b460i-mac26
bash scripts/build_new_efi.sh
python3 scripts/build_tahoe_config.py \
  efi-backup/original-20260830/EFI/OC/config.plist \
  tools/oc-1.0.7/Docs/Sample.plist \
  efi-new/tahoe-oc107/EFI efi-new/tahoe-oc107/EFI/OC/config.plist
tools/oc-1.0.7/Utilities/ocvalidate/ocvalidate efi-new/tahoe-oc107/EFI/OC/config.plist
# 注意：build_new_efi.sh 会重建 tahoe-oc107 目录，HeliPort 已放在 efi-new/companion/ 不受影响
```
