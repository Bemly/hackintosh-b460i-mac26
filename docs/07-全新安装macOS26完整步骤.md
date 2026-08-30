# 07 · 全新安装 macOS 26 Tahoe 完整步骤（全盘格 13 → U 盘安装）

> 本文档是 **"直接格式化现有 macOS 13、U 盘引导全新安装 26"** 的完整操作手册。
> 与 `docs/06 §8` 的区别：那边是"先 U 盘验证、不动现网"的保守路线；本文是全盘重装路线，两者共用同一套 `efi-new/tahoe-oc107` 新 EFI。
> 制作日期：2026-08-30。安装器：macOS Tahoe **26.6.2（build 25G83）**，已在 `/Applications/Install macOS Tahoe.app`，完整性已三重验证（dmg CRC32 全盘校验 / Apple 签名链 / 内部元数据版本号）。

---

## 0. 本机磁盘现状（2026-08-30 实测）与 ⚠️ 数据警告

| 磁盘 | 容量 | 内容 | 处置 |
|---|---|---|---|
| **disk0**（内置） | 1 TB | EFI 8.6GB + APFS 容器：`macos`（13 系统，9.3GB）+ **`macos - 数据`（824.7GB）** | **本次要抹掉的就是它** |
| **disk2**（内置） | 12 TB | `游戏`(3TB) / `办公`(587.6GB) / `文档代码`(4TB) / APFS 卷 `MAC`(4.4TB 容器) | **完全不动** |

⚠️ **最大风险点**：disk0 的 APFS 容器里 `macos - 数据` 有 **824.7GB**——你日常的用户文件大概率都在这里（桌面/文稿/下载等都在"数据"卷上）。全盘抹掉 = 这 824.7GB 一起没。**动手前务必确认：这批数据要么已备份到 12TB 盘/网盘，要么确认不要了。**

其他两条硬性注意：
1. 安装器 Disk Utility 里抹盘时**只选 1TB 那块物理盘**，12TB 盘千万别碰。
2. Windows 的盘符数据（游戏/办公/文档代码）在 disk2 上，与本次抹盘无关。

---

## 1. 准备清单

- [ ] U 盘 **≥ 32GB**（建议 64GB、USB3），可整盘清空
- [ ] 个人数据已备份（见上 ⚠️）
- [ ] `/Applications/Install macOS Tahoe.app`（26.6.2，已就位）
- [ ] 新 EFI：`efi-new/tahoe-oc107/EFI/`（OC 1.0.7，含 Tahoe 全套 kext 与调试参数）
- [ ] `efi-new/companion/HeliPort-v1.5.0.dmg`（装完系统后连 WiFi 用）
- [ ] 回滚保险：`efi-backup/original-20260830/` 里存着 13 的原 EFI 原档
- [ ] BIOS 设置无需改动（现网 13 已在此设置下稳定）；仅当以后 CMOS 放电/清空才需要复查：**Above 4G Decoding 开、CSM 关、Secure Boot 关、VT-d 关**（config 里也有 DisableIoMapper 兜底）

---

## 2. 第一步 · 制作安装 U 盘

插上 U 盘后：

```bash
# 1) 确认 U 盘盘符——按容量核对！下文假设是 disk8，以你实际为准
diskutil list external

# 2) 整盘抹成 GPT + Mac OS Extended（日志式），卷名 InstallUSB
#    ⚠️ diskN 一定填 U 盘（按容量辨认），绝不能是 disk0 / disk2
diskutil eraseDisk JHFS+ InstallUSB disk8

# 3) 写入 Tahoe 安装器，约 20–40 分钟，结束卷名自动变为 "Install macOS Tahoe"
sudo "/Applications/Install macOS Tahoe.app/Contents/Resources/createinstallmedia" --volume /Volumes/InstallUSB
```

## 3. 第二步 · 把新 EFI 和 HeliPort 拷上 U 盘

```bash
# 1) 挂载 U 盘的 EFI 分区（disk8 的第 1 个分区，约 200MB）
diskutil mount disk8s1

# 2) 拷入 Tahoe 新 EFI（若 U 盘 ESP 里已有旧 EFI 目录，先删再拷）
sudo rm -rf /Volumes/EFI/EFI
sudo cp -a /Users/user/hackintosh-b460i-mac26/efi-new/tahoe-oc107/EFI /Volumes/EFI/
ls /Volumes/EFI/EFI        # 应看到 Boot + OC 两项

# 3) HeliPort 放在安装盘根目录随 U 盘走，装完系统拷出来安装
cp /Users/user/hackintosh-b460i-mac26/efi-new/companion/HeliPort-v1.5.0.dmg "/Volumes/Install macOS Tahoe/"
```

## 4. 第三步 · 抹盘前先验证 U 盘引导（重要，给自己留后路）

1. 重启 → 主板启动菜单（微星 B460i 一般是 **F11**）→ 选 **UEFI: 你的U盘**。
2. 出现 OpenCore 选择器后应看到两项：`Install macOS Tahoe`（U 盘）和现网 13 的 `macos`。
3. **先选现网 13 正常进一次系统**——证明 U 盘上的 OC 1.0.7 引导链没问题。这一步通过之前，**不要抹盘**。
   - 万一 U 盘 OC 起不来：拔 U 盘照常回 13（内置盘还没动），排查 U 盘 ESP 拷贝是否完整。
4. 验证通过后，此 U 盘从此就是"安装盘 + 救援盘"，长期保留。

## 5. 第四步 · 抹盘并安装

1. 重启 → U 盘 OC → 选 **`Install macOS Tahoe`** → 进入安装器。
2. 先开 **磁盘工具** → 菜单栏"显示"→**显示所有设备**：
   - 选**最顶层的 1TB 物理盘**（不是下面 12TB！）
   - 点"抹掉"：方案 **GUID 分区图**，格式 **APFS**，名称 **Macintosh HD**
   - 确认后 13 和那 824.7GB 一起清空，同时自动生成新的 ESP（约 260MB，旧 8.6GB ESP 一并消失，正常）
3. 退出磁盘工具 → 选 **安装 macOS Tahoe** → 目标 `Macintosh HD`。
4. 第一阶段拷文件约 20–40 分钟，随后自动重启数次。**关键规则：**
   - 每次重启都要**再次从 U 盘引导进 OC**；
   - 第二阶段起在选择器里选 **`macOS Installer`**（这是内置盘上的安装进程），**不要**再选 U 盘的 `Install macOS Tahoe`（选错会重头开始第一阶段）；
   - 重启 2–3 次后该条目会变成 `Macintosh HD`，一直选它直到出现设置助理。
5. 全程开跑码（新 EFI 的 `-v`）属正常；若卡住超 10 分钟，记下最后一行跑码再对照 `docs/04/05` 排查。

## 6. 第五步 · 首次开机

1. **设置助理**：可离线进行——先创建**本地账户**，Apple ID 登录跳过（WiFi 还没管理工具）。
2. 联网（二选一）：
   - 有网线：插上即可（RealtekRTL8111 已带，即插即通）；
   - WiFi：打开 U 盘安装卷根目录的 `HeliPort-v1.5.0.dmg` 安装 → 菜单栏 HeliPort 图标 → 选 WiFi 输密码（itlwm 驱动在新 EFI 里已加载）。
3. 联网后补登 Apple ID；`revpatch=sbvmm` + RestrictEvents 已就位，Tahoe 的 OTA 系统更新可正常收到（见 `docs/06 §7`）。

## 7. 第六步 · EFI 回填内置盘（此后可摆脱 U 盘引导）

```bash
# 1) 分别挂载内置盘新 ESP（disk0s1）与 U 盘 ESP（disk8s1），用固定挂载点名避免重名冲突
diskutil mount disk0s1 -mountPoint /Volumes/ESP-internal
diskutil mount disk8s1 -mountPoint /Volumes/ESP-usb

# 2) 内置盘 ESP 清空后拷入 U 盘上的 Tahoe EFI
sudo rm -rf /Volumes/ESP-internal/EFI
sudo cp -a /Volumes/ESP-usb/EFI /Volumes/ESP-internal/
ls /Volumes/ESP-internal/EFI   # Boot + OC
```

之后重启默认走内置盘 OC（U 盘拔不拔随意，建议保留作救援）。

**调试参数收尾**（稳定运行几天后）：编辑内置盘 `EFI/OC/config.plist`，把 `-v debug=0x100 keepsyms=1` 从 boot-args 移除即可进入静默+苹果Logo 正常模式；**保留** `agdpmod=pikera revpatch=sbvmm -ibtcompatbeta`，ApplePanic/Target 建议保留以便日后取证。改完用 `tools/oc-1.0.7` 里的 ocvalidate 校验。

## 8. 验收清单

- [ ] 关于本机：Mac Tahoe 26.6.2，显卡 RX 6800 显存识别正常（加速生效）
- [ ] WiFi：HeliPort 可选网、可上网
- [ ] 蓝牙：能搜到设备（社区 fork 2.5.1 + `-ibtcompatbeta`）
- [ ] 音频：显示器喇叭/耳机（DP/HDMI 数字音频）正常；**板载模拟音频在 Tahoe 已知受限**（`docs/06 §5`），USB 声卡/蓝牙耳机可用
- [ ] USB 全端口可用（USBPorts 本机定制件已迁移）
- [ ] 温度传感器读数正常（显卡温度 kext 已迁移）
- [ ] 系统设置 → 软件更新：能检测到后续 OTA

## 9. 回滚预案

- **抹盘前**任何时刻出问题：拔 U 盘回 13；U 盘 OC 坏了就检查其 ESP 拷贝。
- **装到一半**崩溃：用 U 盘 OC 重进安装器重来即可（盘已清空，无损失）。
- **26 用不下去想回 13**：需重做 13 安装 U 盘（Ventura 全量安装器可再下载），把 `efi-backup/original-20260830` 的原 EFI 写回 ESP；12TB 盘数据不受影响。
- **系统盘引导彻底异常**：只要 U 盘在，永远可用 U 盘 OC 引导应急。
