# macOS 15 黑屏复盘 & macOS 26 (Tahoe) 升级评估与排查方案

> 生成时间：2026-08-30
> 机器：七彩虹 CVN B460I GAMING FROZEN + i5-10400 + RX6800，现用 macOS 13.7.8，OpenCore 0.9.1（上游 2023-05-15 / Release 3.3.0）

---

## 一、结论先行

1. **用现在这套 EFI（OC 0.9.1 + 2023 年初的 kext）直接升 macOS 26，必然失败**——表现会和你当年升 macOS 15 一样黑屏（甚至更早卡死）。这不是运气问题，是引导器和驱动整体落后系统 3 年。
2. **但你的硬件本身完全可以跑 macOS 26**。i5-10400（Comet Lake）+ RX6800（RDNA2）+ iMac20,1 正是 macOS 26 Tahoe 社区公认的成熟"养老组合"；Tahoe 是**最后一代支持 Intel 的 macOS**，这类机器反而是长期支持对象。
3. 正确路径是：**先把 OpenCore 升到 1.0.7、全部 kext 升到 Tahoe 对应版本 → 用新 EFI 先在 U 盘上试引导现有 13 系统 → 再做安装盘升级 26**。本次已先把开机改成跑码模式，下次任何启动失败都能看到卡在哪一行，而不是对着黑屏猜。

---

## 二、当年升 macOS 15 黑屏的根因分析（按可能性排序）

macOS 15 Sequoia 发布于 2024-09，而你的 EFI 停在 2023-05，差距 16 个月，以下问题**叠加存在**：

### 根因 1（主因）：OpenCore 0.9.1 根本不认识 macOS 15 的内核
- OpenCore 版本与系统对应关系：0.9.1（2023-04，Ventura 时代）→ 1.0.0（2024-05）→ **1.0.1/1.0.2（2024-08/10，Sequoia 配套）** → 1.0.7（2026-03，Tahoe 26.4+ 配套）。
- 旧 OC 引导新内核时，缺少新系统要求的内核补丁/Quirk 处理，典型表现就是：进度条走一段后**黑屏、无输出、自动断电重启**。
- 佐证：同一位上游作者在 2024-11-16 发布的 4.0.0 版 EFI 已把 OC 换成 1.0.2（文件时间戳 2024-10-08，与 OC 1.0.2 发布日一致），说明作者本人也是升到 1.0.x 才解决 Sequoia 引导。

### 根因 2：Lilu / WhateverGreen 1.6.4 不支持 Sequoia
- Sequoia 重写了大量图形/内核接口，**Lilu、WhateverGreen 至少要 1.6.7/1.6.8 起步**（Tahoe 需 Lilu 1.7.x、WEG 1.7.0）。
- 你的 RX6800 虽然是原生免驱卡，但它在黑苹果下仍要经过 WhateverGreen 的 `agdpmod=pikera` 补丁链；旧 WEG 在新内核上补丁链失效，** board-id 显卡协商阶段直接黑屏**——这与"logo 出现后黑屏"的特征高度吻合。

### 根因 3：itlwm 2.1.0 是 Ventura 专用版
- 2.1.0 只匹配 macOS 13 的网络内核框架；在 15 上加载会直接内核恐慌（Kernel Panic）。没开 `-v` 时，panic 画面你看不到，外在表现就是**黑屏或反复重启**。

### 根因 4（次要）：SecureBootModel 值不匹配
- 当前 `SecureBootModel=j185f`，而 j185f 实际对应 **iMac20,2**；你的 SMBIOS 是 **iMac20,1，对应值应为 j185**。Sequoia/Tahoe 对 Apple 安全启动模型校验更严格，值对不上可能在更新验证阶段被拦下。上游 4.0.0 已直接改为 `Disabled` 规避，这也是推荐做法。

### 根因 5（放大问题）：当时没有任何取证手段
- 原配置 `Misc/Debug`：AppleDebug=False、ApplePanic=False、**Target=0（不写日志）**，boot-args 也没有 `-v`。所以失败时既看不到跑码，EFI 里也不会留下 panic 和 OC 日志，无法定位——这正是本次先解决的问题。

> 核显不是嫌疑：你的 UHD630 是 headless（0x3E920003）且不接显示器，显示输出全在原生免驱的 RX6800 上，不存在核显 framebuffer 黑屏问题。

---

## 三、macOS 26 Tahoe 逐硬件兼容性评估

| 硬件 | Tahoe 26 兼容性 | 说明 / 需要做的事 |
|---|---|---|
| i5-10400（Comet Lake-S） | ✅ 原生支持到 Tahoe（最后一代） | iMac20,1 继续使用；SSDT 补丁集无需改动 |
| RX6800 16GB（RDNA2） | ✅ 原生免驱，Metal 3 完整 | 保留 `agdpmod=pikera`；更新 WhateverGreen 1.7.0 |
| UHD630 headless | ✅ 可用 | 保持 0x3E920003；WEG 1.7.0 已修复 Tahoe 核显问题 |
| ALC662 声卡 | ✅ 可用 | AppleALC 升到 1.9.7，layout-id=7 不变 |
| RTL8111 有线网卡 | ✅ 可用 | RealtekRTL8111 升最新（2.5.x） |
| AX200 WiFi（itlwm 路线） | ✅ 可用，但必须换驱动 | itlwm 升到支持 Tahoe 的版本（v2.3.0 起步，Tahoe 26.5+ 建议用 OpenIntelWireless 最新 CI 构建）+ 同步更新 HeliPort。你选的纯 itlwm 路线**不需要 OCLP 根补丁**，比 AirportItlwm 路线省事 |
| AX200 蓝牙 | ⚠️ 可用，需更新三件套 | IntelBluetoothFirmware + IntelBTPatcher 用最新版，BlueToolFixup 用 BrcmPatchRAM 最新；社区在 Tahoe 26.5+ 已验证配对/连接恢复 |
| USB 定制（USBPorts.kext） | ✅ 沿用 | 15 端口映射与系统版本无关，继续用；XhciPortLimit 保持 False |
| CPUFriend 变频 | ✅ 可用 | 升到 1.2.9+，DataProvider 不变 |
| NVMe（白泽 1TB） | ✅ 可用 | NVMeFix 1.1.3 |
| RadeonSensor/SMCRadeonGPU、SMC* | ✅ 可用 | 全部换最新即可 |

**结论：没有任何一个硬件是 Tahoe 的拦路虎，全部工作都是"换软件版本"。**

---

## 四、版本差距对照表（当前 → 升级 26 需要）

| 组件 | 当前（2023-05） | macOS 26 所需（2026-08 现状） |
|---|---|---|
| OpenCore | 0.9.1 | **1.0.7**（2026-03-20，已下载到 tools/oc-1.0.7） |
| Lilu | 1.6.4 | **1.7.2** |
| WhateverGreen | 1.6.4 | **1.7.0** |
| AppleALC | 1.8.1 | **1.9.7** |
| VirtualSMC 全家桶 | 1.3.1 | **1.3.7** |
| NVMeFix | 1.1.0 | **1.1.3** |
| CPUFriend | 1.2.6 | **1.2.9+** |
| itlwm | 2.1.0（Ventura 专用） | **2.3.0 或 Tahoe 适配的最新构建** |
| IntelBluetooth 三件套 | 2.2.0 / 2.6.5 | 最新 Release（Tahoe 适配） |
| RealtekRTL8111 | 2.4.2 | 2.5.x 最新 |
| SecureBootModel | j185f（值错配） | **Disabled**（升级期推荐，与上游 4.0.0 一致） |
| boot-args | `-v agdpmod=pikera keepsyms=1 debug=0x100`（本次已改） | 首次装 beta/新版 kext 未齐时临时加 `-lilubetaall`，正式版齐了去掉 |

---

## 五、本次已完成的"跑码取证"改造（已部署到 EFI）

只改了 `EFI/OC/config.plist` 一个文件，其他文件原封不动，已通过 ocvalidate 0.9.1 校验（0 问题）：

1. `boot-args` 增加 **`-v`**：开机不再是苹果 logo + 进度条，改为全屏幕文字跑码，卡在哪一行一目了然。
2. `Misc/Debug/AppleDebug = true`：向内核传递调试启动信息。
3. `Misc/Debug/ApplePanic = true`：**一旦内核恐慌，自动把 `panic-xxxx.txt` 写到 EFI 分区根目录**，黑屏/重启后挂载 EFI 就能取到最后一屏证据。
4. `Misc/Debug/Target = 67`：OpenCore 自身日志 `opencore-xxxx.txt` 落盘到 EFI 根目录。
5. 补齐 2 个缺失键（GopBurstMode、ResizeUsePciRbIo，安全默认值，不改行为）。

**下次再遇到黑屏，请这样取证：**
1. 手机拍下屏幕最后 20 行跑码（重点找 `panic`、`failed`、`waiting for`、`Couldn't allocate` 字样）；
2. 强制重启后进 macOS（或用另一台机器/PE）挂载 EFI，把根目录的 `panic-*.txt`、`opencore-*.txt` 拿出来；
3. 把这些发给我，就能精确定位是哪个 kext / 哪个阶段挂的。

**回滚方法（两重保险）：**
- EFI 分区上已留 `EFI/OC/config.plist.bak-before-verbose`，想恢复 logo 开机，挂载 EFI 后用它覆盖 config.plist 即可；
- 工作目录 `efi-backup/original-20260830/` 是整套原始 EFI 副本，且已进 git 历史，随时可整体还原。

---

## 六、推荐升级路线（安全优先，分步可回退）

### 阶段 A：先在不动系统的前提下把 EFI 升到 1.0.7（建议下一步就做）
1. 以 `tools/oc-1.0.7/X64/EFI` 为模板替换 OC 主体（OpenCore.efi、Boot/BOOTx64.efi、Drivers 里的 OpenRuntime/OpenCanopy，保留 HfsPlus）；
2. Kexts 按第四节全部换新，**ACPI 10 个 SSDT、USBPorts.kext、CPUFriendDataProvider、你的三码 SMBIOS 全部保留**；
3. config 用 ProperTree 的 OC Clean Snapshot 重建结构后，逐项核对（或用 OCConfigCompare 对比 1.0.7 的 sample.plist 补全新字段），SecureBootModel 改 Disabled；
4. 用 **1.0.7 的 ocvalidate 校验到 0 issue**；
5. **先放 U 盘 EFI，开机按 F11 选 U 盘引导，验证能否正常进入现在的 macOS 13**——这一步零风险，验证新引导的兼容性。

### 阶段 B：试引导通过后，再升级系统
1. Time Machine 完整备份（12TB 数据盘上的 MAC 卷可作为目标之一，但系统盘备份建议独立外置盘）；
2. 制作 macOS 26 安装 U 盘（`createinstallmedia`）；
3. 用新 EFI 引导安装盘，**全程 -v 跑码观察**；建议先升级到最新 Tahoe 小版本（26.5+，蓝牙/WiFi 修复更完整）；
4. 装完进系统后再更新 HeliPort、检查 WiFi/蓝牙/声音/隔空投送等；
5. 全部稳定后，可去掉 `-v`（改回 logo 开机），Target 调回 0，ApplePanic 可保留。

### 需要你确认的决策点
- [ ] 是否现在就让我按阶段 A 制作一套 **OC 1.0.7 + 最新 kext 的新 EFI**（先放工作目录和 U 盘，不覆盖现网）？
- [ ] WiFi 维持 itlwm + HeliPort 路线（推荐，免根补丁），还是想趁升级换博通免驱网卡（接近白苹果体验，需要硬件成本）？
- [ ] 是否保留 OpenCanopy 图形引导菜单（跑码只影响内核阶段，不影响菜单）？

---

## 七、参考来源

- OpenCorePkg Releases（版本时间线/1.0.7）：https://github.com/acidanthera/OpenCorePkg/releases
- 上游 EFI 仓库与 Release（3.3.0=2023-05-15 现用版，4.0.0=2024-11 Sequoia 版）：https://github.com/anlostsheep/hackintosh-colorful-b460i
- Comet Lake 桌面各 SMBIOS 对 Tahoe 支持矩阵：https://github.com/So1jon/Hackintosh-Desktop-Comet-Lake
- macOS 26 Tahoe 为末代 Intel 系统、Comet Lake+RX6000 兼容说明：https://zeerawireless.com/tr/blogs/news/macos-26-tahoe-explained-final-update-for-intel-macs-opencore-hackintosh-impacts
- OpenCore 1.0.7 对 Tahoe 26.4 的必要性：https://www.pixbugtech.com/content/site_content/1093063e-2453-4241-94d8-0aabf71dba5a
- Intel AX 网卡 Tahoe 状态报告（itlwm/蓝牙 26.5+ 验证）：https://github.com/OpenIntelWireless/itlwm/issues/1062
- AirportItlwm 在 Sequoia/Tahoe 需 OCLP-Mod 的说明（反衬纯 itlwm 更省事）：https://github.com/5T33Z0/OCLP4Hackintosh/blob/main/Enable_Features/AirportItllwm_Sequoia.md
- SecureBootModel 与 SMBIOS 对应关系（j185=iMac20,1，j185f=iMac20,2）：https://www.insanelymac.com/forum/topic/360295-securebootmodel-in-opencore/
- 黑苹果图形问题速查表（verbose 后黑屏=framebuffer 问题等）：https://deepwiki.com/dortania/OpenCore-Install-Guide/7.3-graphics-and-display-issues
