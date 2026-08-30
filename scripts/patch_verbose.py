#!/usr/bin/env python3
"""
patch_verbose.py —— 给 OpenCore config.plist 开启 verbose 跑码与调试取证
用法: python3 patch_verbose.py <输入config.plist> <输出config.plist>

只做以下最小改动，其他键值一律保持不变:
1. NVRAM/Add/7C43.../boot-args 增加 "-v"（内核跑码，替代苹果 logo 进度条）
2. Misc/Debug: AppleDebug=True, ApplePanic=True, Target=67
   - Target=67(0x43): 启用日志 + 写 DataHub + 日志文件落盘到 EFI 卷根(opencore-*.txt)
   - ApplePanic: 内核 panic 自动保存 panic-*.txt 到 EFI 卷根，黑屏/重启后可取证
3. 补齐 ocvalidate 0.9.1 报缺失的两个键: UEFI/Output/GopBurstMode=False
   与 UEFI/Quirks/ResizeUsePciRbIo=False（均为该版本安全默认值，不改变行为）
"""
import plistlib, sys

NVRAM_GUID = '7C436110-AB2A-4BBB-A880-FE41995C9F82'

def main(src, dst):
    with open(src, 'rb') as f:
        c = plistlib.load(f)

    changes = []

    # 1) boot-args 增加 -v
    nv = c['NVRAM']['Add'][NVRAM_GUID]
    args = nv.get('boot-args', '') or ''
    tokens = args.split()
    if '-v' not in tokens:
        nv['boot-args'] = ('-v ' + args).strip()
        changes.append(f'boot-args: "{args}" -> "{nv["boot-args"]}"')
    else:
        print('[skip] boot-args 已含 -v')

    # 2) Misc/Debug 调试开关
    dbg = c['Misc']['Debug']
    for key, val in [('AppleDebug', True), ('ApplePanic', True), ('Target', 67)]:
        old = dbg.get(key)
        if old != val:
            dbg[key] = val
            changes.append(f'Misc/Debug/{key}: {old} -> {val}')

    # 3) 补齐缺失键（安全默认值）
    out = c['UEFI'].setdefault('Output', {})
    if 'GopBurstMode' not in out:
        out['GopBurstMode'] = False
        changes.append('UEFI/Output/GopBurstMode: 缺失 -> False')
    q = c['UEFI'].setdefault('Quirks', {})
    if 'ResizeUsePciRbIo' not in q:
        q['ResizeUsePciRbIo'] = False
        changes.append('UEFI/Quirks/ResizeUsePciRbIo: 缺失 -> False')

    with open(dst, 'wb') as f:
        plistlib.dump(c, f, fmt=plistlib.FMT_XML)

    print('修改清单:')
    for x in changes:
        print('  -', x)
    print(f'已写出: {dst}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
