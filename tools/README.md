# 引导修改工具说明（本目录二进制不入库，按下列地址重新获取）

网络代理：`http://127.0.0.1:7890`（git 已在仓库级配置 http/https.proxy）

## 已下载的工具

| 工具 | 版本 | 本地路径 | 下载来源 | 用途 |
|---|---|---|---|---|
| OpenCorePkg RELEASE | 0.9.1（与现网 EFI 同版本） | `tools/oc-0.9.1/` | https://github.com/acidanthera/OpenCorePkg/releases/download/0.9.1/OpenCore-0.9.1-RELEASE.zip | 用其 `Utilities/ocvalidate` 精确校验当前 config；升级对照基线 |
| OpenCorePkg RELEASE | 1.0.7（2026-03-20，最新，支持 macOS 26 Tahoe） | `tools/oc-1.0.7/` | https://github.com/acidanthera/OpenCorePkg/releases/download/1.0.7/OpenCore-1.0.7-RELEASE.zip | 升级 macOS 26 时的引导主体、X64/EFI 驱动与新版 ocvalidate |
| ProperTree | master（git clone） | `tools/ProperTree/` | https://github.com/corpnewt/ProperTree | config.plist 图形/脚本编辑（`python3 ProperTree.command`），Scripts 内含 OCConfigCompare |

原始 zip 保留在 `tools/_downloads/`（已 gitignore）。

## 常用命令

```bash
# 校验 config（版本必须与所用 OpenCore 大版本一致）
tools/oc-0.9.1/Utilities/ocvalidate/ocvalidate <config.plist>
tools/oc-1.0.7/Utilities/ocvalidate/ocvalidate <config.plist>

# 挂载 EFI 分区（需要管理员密码）
sudo diskutil mount disk0s1
# 只读挂载：sudo diskutil mount readOnly disk0s1

# plist 格式互转
plutil -convert xml1 config.plist    # 转文本 XML（便于 git diff）
plutil -convert binary1 config.plist # 转二进制
plutil -lint config.plist            # 语法检查
```

## macOS 26 升级时还需获取的 Kext（均走代理从 GitHub Release 下载）

| Kext | 仓库 | 备注 |
|---|---|---|
| Lilu / WhateverGreen / AppleALC / VirtualSMC(含 SMCProcessor/SMCSuperIO) / NVMeFix / CPUFriend | github.com/acidanthera | Tahoe 需 Lilu ≥1.7.x、WEG ≥1.7.0 |
| itlwm（纯 itlwm 路线，配 HeliPort） | github.com/OpenIntelWireless/itlwm/releases | **必须下载对应 macOS 26 的版本**，2.1.0 只支持 Ventura |
| IntelBluetoothFirmware + IntelBTPatcher + BlueToolFixup(BrcmPatchRAM) | github.com/OpenIntelWireless / acidanthera/BrcmPatchRAM | Tahoe 26.5+ 已恢复可用 |
| RealtekRTL8111 | github.com/Miezy/RealtekRTL8111 | 取最新 |
| RadeonSensor / SMCRadeonGPU | github.com/aluveitie/RadeonSensor | 取最新 |
| XHCI-unsupported | github.com/RehabMan/NoTouchID 等（acidanthera 镜像） | 一般可沿用 |
