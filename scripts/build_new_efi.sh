#!/bin/bash
# build_new_efi.sh —— 组装面向 macOS 26 Tahoe 的全新 EFI（OC 1.0.7 + 最新 kext）
# 可重复执行；本机定制件(SSDT/USB定制/变频数据/主题/三码)来自旧 EFI 备份
set -e
ROOT=~/hackintosh-b460i-mac26
OLD="$ROOT/efi-backup/original-20260830/EFI"
OC="$ROOT/tools/oc-1.0.7/X64/EFI"
STG="$ROOT/tools/_downloads/staging"
OUT="$ROOT/efi-new/tahoe-oc107/EFI"

rm -rf "$(dirname "$OUT")"
mkdir -p "$OUT/Boot" "$OUT/OC"/{ACPI,Drivers,Kexts,Tools,Resources}

# 1) OpenCore 1.0.7 主体
cp "$OC/BOOT/BOOTx64.efi" "$OUT/Boot/"
cp "$OC/BOOT/.contentFlavour" "$OC/BOOT/.contentVisibility" "$OUT/Boot/" 2>/dev/null || true
cp "$OC/OC/OpenCore.efi" "$OC/OC/.contentFlavour" "$OC/OC/.contentVisibility" "$OUT/OC/" 2>/dev/null || true

# 2) Drivers（精选：运行时/图形菜单/HFS/重置NVRAM/截图；HFS 用官方 OpenHfsPlus 替代旧闭源 HfsPlus）
for d in OpenRuntime OpenCanopy OpenHfsPlus ResetNvramEntry CrScreenshotDxe; do
  cp "$OC/OC/Drivers/$d.efi" "$OUT/OC/Drivers/"
done

# 3) Tools（排障用 UEFI Shell 与 SIP 工具）
cp "$OC/OC/Tools/OpenShell.efi" "$OC/OC/Tools/CsrUtil.efi" "$OUT/OC/Tools/"

# 4) ACPI：沿用本机 10 个 SSDT
cp "$OLD/OC/ACPI/"*.aml "$OUT/OC/ACPI/"

# 5) Kexts —— 全新下载的 Tahoe 适配版本
cp -R "$STG/Lilu-1.7.2/Lilu.kext" "$OUT/OC/Kexts/"
cp -R "$STG/VirtualSMC-1.3.7/Kexts/VirtualSMC.kext" "$OUT/OC/Kexts/"
cp -R "$STG/VirtualSMC-1.3.7/Kexts/SMCProcessor.kext" "$OUT/OC/Kexts/"
cp -R "$STG/VirtualSMC-1.3.7/Kexts/SMCSuperIO.kext" "$OUT/OC/Kexts/"
cp -R "$STG/WhateverGreen-1.7.0/WhateverGreen.kext" "$OUT/OC/Kexts/"
cp -R "$STG/AppleALC-1.9.7/AppleALC.kext" "$OUT/OC/Kexts/"
cp -R "$STG/NVMeFix-1.1.3/NVMeFix.kext" "$OUT/OC/Kexts/"
cp -R "$STG/CPUFriend-1.3.0/CPUFriend.kext" "$OUT/OC/Kexts/"
cp -R "$STG/itlwm-v2.3.0-stable/itlwm.kext" "$OUT/OC/Kexts/"
cp -R "$STG/IntelBluetooth-v2.4.0/IntelBluetoothFirmware.kext" "$OUT/OC/Kexts/"
cp -R "$STG/IntelBluetooth-v2.4.0/IntelBTPatcher.kext" "$OUT/OC/Kexts/"
cp -R "$STG/BrcmPatchRAM-2.7.2/BlueToolFixup.kext" "$OUT/OC/Kexts/"
cp -R "$STG/RealtekRTL8111-V3.0.0/RealtekRTL8111-V3.0.0/Release/RealtekRTL8111.kext" "$OUT/OC/Kexts/"

# 6) Kexts —— 沿用本机定制件（不可替换：端口映射/变频数据/显卡温度，无更新版本）
cp -R "$OLD/OC/Kexts/USBPorts.kext" "$OUT/OC/Kexts/"
cp -R "$OLD/OC/Kexts/CPUFriendDataProvider.kext" "$OUT/OC/Kexts/"
cp -R "$OLD/OC/Kexts/RadeonSensor.kext" "$OUT/OC/Kexts/"
cp -R "$OLD/OC/Kexts/SMCRadeonGPU.kext" "$OUT/OC/Kexts/"

# 7) Resources 主题资源（字体/图标/音频），跨 OC 版本兼容，沿用
ditto "$OLD/OC/Resources" "$OUT/OC/Resources"

# 8) 清理 FAT 复制产生的 AppleDouble 垃圾
find "$OUT" -name '._*' -delete
find "$OUT" -name '.DS_Store' -delete

echo "组装完成: $OUT"
