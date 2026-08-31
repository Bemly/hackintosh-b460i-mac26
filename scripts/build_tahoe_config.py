#!/usr/bin/env python3
"""
build_tahoe_config.py —— 基于旧 config + OC 1.0.7 Sample.plist 生成 Tahoe 全新 config
- 继承旧 config 的全部本机定制：SSDT、DeviceProperties、Quirks 调优、三码 SMBIOS、NVRAM
- 补齐 1.0.7 新增键默认值，删除已废弃键(Misc/Serial/Custom)
- 按依赖顺序重建 Kernel/Add（自动读取新 EFI 的 kext 与可执行文件路径）
- 重建 UEFI/Drivers、Misc/Tools
- 强制: boot-args 带 -v；AppleDebug/ApplePanic=True、Target=67；SecureBootModel=Disabled
用法: build_tahoe_config.py <旧config> <1.0.7 Sample.plist> <新EFI目录> <输出config>
"""
import plistlib, sys, os, copy

# Kext 加载顺序（Lilu 及其依赖在前；codeless kext 无二进制）
KEXT_ORDER = [
    'Lilu.kext',
    'VirtualSMC.kext',
    'SMCProcessor.kext',
    'SMCSuperIO.kext',
    'WhateverGreen.kext',
    'AppleALC.kext',
    'CPUFriend.kext',
    'CPUFriendDataProvider.kext',
    'NVMeFix.kext',
    'itlwm.kext',
    'IntelBluetoothFirmware.kext',
    'IntelBTPatcher.kext',
    'BlueToolFixup.kext',
    'RestrictEvents.kext',
    'RealtekRTL8111.kext',
    'RadeonSensor.kext',
    'SMCRadeonGPU.kext',
    'USBPorts.kext',
]
KEXT_COMMENT = {
    'Lilu.kext': 'v1.7.2 patch engine',
    'VirtualSMC.kext': 'v1.3.7 SMC emulator',
    'SMCProcessor.kext': 'v1.3.7 CPU temp',
    'SMCSuperIO.kext': 'v1.3.7 fan sensors',
    'WhateverGreen.kext': 'v1.7.0 graphics patches for Tahoe',
    'AppleALC.kext': 'v1.9.7 ALC662 layout-id 7',
    'CPUFriend.kext': 'v1.3.0 power management',
    'CPUFriendDataProvider.kext': 'local CPUFriend data profile',
    'NVMeFix.kext': 'v1.1.3 NVMe fixes',
    'itlwm.kext': 'v2.3.0 Intel AX200 WiFi (use with HeliPort)',
    'IntelBluetoothFirmware.kext': 'v2.5.1 AX200 BT firmware (Tahoe fork)',
    'IntelBTPatcher.kext': 'v2.5.1 Intel BT patcher (Tahoe fork)',
    'BlueToolFixup.kext': 'v2.7.2 BT fix for Monterey+',
    'RestrictEvents.kext': 'v1.1.6 OTA with revpatch=sbvmm',
    'RealtekRTL8111.kext': 'v3.0.0 RTL8111 (Tahoe AppleVTD)',
    'RadeonSensor.kext': 'v0.3.3 RX6800 temp',
    'SMCRadeonGPU.kext': 'v0.3.3 RX6800 GPU sensor',
    'USBPorts.kext': 'local USB port map',
}
DRIVERS = [
    ('OpenRuntime.efi', False, 'runtime services'),
    ('OpenCanopy.efi', False, 'graphical picker'),
    ('OpenHfsPlus.efi', False, 'open-source HFS driver'),
    ('ResetNvramEntry.efi', False, 'reset NVRAM entry'),
    ('CrScreenshotDxe.efi', False, 'boot screenshot'),
]

def merge_defaults(t, s, path=''):
    """用 sample s 递归补齐 target t 缺失键；不碰 # 注释键与列表；保留 t 已有值。"""
    if not isinstance(t, dict) or not isinstance(s, dict):
        return
    for k, sv in s.items():
        if str(k).startswith('#'):
            continue
        if k not in t:
            t[k] = copy.deepcopy(sv)
        elif isinstance(t[k], dict) and isinstance(sv, dict):
            merge_defaults(t[k], sv, f'{path}/{k}')

def find_executable(kext_path):
    macos = os.path.join(kext_path, 'Contents', 'MacOS')
    if os.path.isdir(macos):
        bins = [f for f in os.listdir(macos) if not f.startswith('._')]
        if len(bins) == 1:
            return f'Contents/MacOS/{bins[0]}'
    return ''  # codeless kext

def build_kernel_add(efi_dir):
    kdir = os.path.join(efi_dir, 'OC', 'Kexts')
    add = []
    for name in KEXT_ORDER:
        kpath = os.path.join(kdir, name)
        assert os.path.isdir(kpath), f'缺少 kext: {name}'
        add.append({
            'Arch': 'Any',
            'BundlePath': name,
            'Comment': KEXT_COMMENT.get(name, ''),
            'Enabled': True,
            'ExecutablePath': find_executable(kpath),
            'MaxKernel': '',
            'MinKernel': '',
            'PlistPath': 'Contents/Info.plist',
        })
    present = {d for d in os.listdir(kdir) if d.endswith('.kext')}
    missing = present - set(KEXT_ORDER)
    assert not missing, f'存在未纳入顺序表的 kext: {missing}'
    return add

def build_drivers():
    return [{'Arguments': '', 'Comment': c, 'Enabled': True, 'LoadEarly': early, 'Path': p}
            for p, early, c in DRIVERS]

def build_tools():
    return [
        {'Arguments': '', 'Auxiliary': True, 'Comment': 'UEFI shell for debug', 'Enabled': True,
         'Flavour': 'OpenShell:UEFIShell:Shell', 'FullNvramAccess': True, 'Name': 'UEFI Shell',
         'Path': 'OpenShell.efi', 'RealPath': False, 'TextMode': False},
        {'Arguments': '', 'Auxiliary': True, 'Comment': 'SIP toggle utility', 'Enabled': True,
         'Flavour': 'Auto', 'FullNvramAccess': False, 'Name': 'SIP Utility',
         'Path': 'CsrUtil.efi', 'RealPath': False, 'TextMode': False},
    ]

def main(old_p, sample_p, efi_dir, out_p):
    old = plistlib.load(open(old_p, 'rb'))
    sam = plistlib.load(open(sample_p, 'rb'))

    # 整体保留、不参与默认合并的定制块
    keep_devprop = copy.deepcopy(old['DeviceProperties'])
    keep_acpi_add = copy.deepcopy(old['ACPI']['Add'])

    # 1) 递归补全默认值（列表不动）
    merge_defaults(old, sam)

    # 2) 删除 1.0.7 已废弃的键
    old.get('Misc', {}).get('Serial', {}).pop('Custom', None)

    # 3) 还原定制块
    old['DeviceProperties'] = keep_devprop
    old['ACPI']['Add'] = keep_acpi_add
    old['ACPI']['Delete'] = []
    old['ACPI']['Patch'] = old['ACPI'].get('Patch', [])

    # 4) 重建三大列表
    old['Kernel']['Add'] = build_kernel_add(efi_dir)
    old['UEFI']['Drivers'] = build_drivers()
    old['Misc']['Tools'] = build_tools()

    # 5) 调试/跑码（用户明确要求）
    old['Misc']['Debug']['AppleDebug'] = True
    old['Misc']['Debug']['ApplePanic'] = True
    old['Misc']['Debug']['Target'] = 67
    old['Misc']['Debug']['DisableWatchDog'] = True

    # 6) boot-args：-v 跑码 + Tahoe 必需参数（-ibtcompatbeta 蓝牙、revpatch=sbvmm OTA）
    nv = old['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']
    required = ['-v', '-ibtcompatbeta', 'revpatch=sbvmm']
    args = (nv.get('boot-args') or '').split()
    args = [a for a in args if a not in required]
    nv['boot-args'] = ' '.join(required + args)

    # 6.1) Intel 蓝牙在 Monterey+ 所需的 NVRAM 标记（防止系统按第三方 dongle 关闭内置蓝牙）
    nv['bluetoothExternalDongleFailed'] = bytes([0])
    nv['bluetoothInternalControllerInfo'] = bytes(16)

    # 6.2) GPU BAR 固定 8GB（RX 6800 16G；Navi GDDR6 训练 panic 的已知缓解项）
    nv['ResizeAppleGpuBars'] = '8'

    # 7) SecureBootModel 关闭（Tahoe 升级期最稳，与上游 4.0.0 一致）
    old['Misc']['Security']['SecureBootModel'] = 'Disabled'
    # 保险库保持可选，扫描策略 0(全部)
    old['Misc']['Security']['Vault'] = 'Optional'
    old['Misc']['Security']['ScanPolicy'] = 0

    # 8) NVRAM 写回开关
    old['NVRAM']['WriteFlash'] = True

    with open(out_p, 'wb') as f:
        plistlib.dump(old, f, fmt=plistlib.FMT_XML)
    print('已生成:', out_p)
    print('boot-args =', nv['boot-args'])
    print('Kernel/Add kext 数:', len(old['Kernel']['Add']), '| Drivers:', len(old['UEFI']['Drivers']), '| Tools:', len(old['Misc']['Tools']))

if __name__ == '__main__':
    main(*sys.argv[1:5])
