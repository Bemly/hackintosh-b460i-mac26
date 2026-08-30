#!/usr/bin/env python3
# 提取 OpenCore config.plist 关键配置，用法: analyze_config.py <config.plist>
import plistlib, sys, json

def load(p):
    with open(p,'rb') as f: return plistlib.load(f)

def g(d, *path, default='<缺失>'):
    cur = d
    for k in path:
        if isinstance(cur, dict) and k in cur: cur = cur[k]
        else: return default
    return cur

def main(path):
    c = load(path)
    out = []
    P = lambda *a, **kw: g(c,*a,**kw)
    out.append("## ACPI")
    for a in P('ACPI','Add',default=[]):
        out.append(f"  [{'启用' if a.get('Enabled') else '禁用'}] {a.get('Path')}")
    out.append("## Booter/Quirks")
    for k,v in P('Booter','Quirks',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## DeviceProperties")
    for dev,props in P('DeviceProperties','Add',default={}).items():
        out.append(f"  设备 {dev}")
        for k,v in props.items():
            if isinstance(v,bytes): v = '<'+v.hex()+'>'
            out.append(f"     {k} = {v}")
    out.append("## Kernel/Add (kext 加载顺序与启用)")
    for i,k in enumerate(P('Kernel','Add',default=[])):
        out.append(f"  {i:2}. [{'x' if k.get('Enabled') else ' '}] {k.get('BundlePath'):45} MinK={k.get('MinKernel','-'):10} MaxK={k.get('MaxKernel','-')} ExecPath={k.get('ExecutablePath','-')}")
    out.append("## Kernel/Quirks")
    for k,v in P('Kernel','Quirks',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## Misc/Boot")
    for k,v in P('Misc','Boot',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## Misc/Debug")
    for k,v in P('Misc','Debug',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## Misc/Security")
    for k,v in P('Misc','Security',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## NVRAM")
    for guid,entries in P('NVRAM','Add',default={}).items():
        out.append(f"  GUID {guid}")
        for k,v in entries.items():
            if isinstance(v,bytes): v = '<'+v.hex()+'>'
            out.append(f"     {k} = {v}")
    out.append("## PlatformInfo/Generic")
    for k,v in P('PlatformInfo','Generic',default={}).items():
        if isinstance(v,bytes): v = '<'+v.hex()+'>'
        out.append(f"  {k} = {v}")
    out.append("## UEFI/Drivers")
    for d in P('UEFI','Drivers',default=[]):
        if isinstance(d,dict): out.append(f"  [{'x' if d.get('Enabled') else ' '}] {d.get('Path')}")
        else: out.append(f"  {d}")
    out.append("## UEFI/APFS")
    for k,v in P('UEFI','APFS',default={}).items(): out.append(f"  {k} = {v}")
    out.append("## UEFI/Quirks")
    for k,v in P('UEFI','Quirks',default={}).items(): out.append(f"  {k} = {v}")
    print("\n".join(out))

if __name__ == '__main__': main(sys.argv[1])
