# hackintosh-b460i-mac26

七彩虹 B460I + i5-10400 + RX6800 黑苹果：现网 EFI 备份、macOS 15 黑屏复盘、macOS 26 (Tahoe) 升级评估与引导改造工作区。所有改动均提交 git。

## 目录结构

```
hackintosh-b460i-mac26/
├── hardware/01-硬件清单.md            # 本机全部硬件型号/ID/驱动方式总表
├── efi-backup/original-20260830/     # 现网 EFI 完整只读基线（=上游 3.3.0/2023-05-15 + 本机改动）
├── efi-work/verbose-20260830/        # verbose 跑码工作副本（已部署到 EFI）
│   ├── EFI/                          # 实际部署的 EFI 内容
│   └── deploy前-config.plist.*.bak   # 部署前从 EFI 取回的原始 config
├── docs/
│   ├── 02-config-原始配置全量.txt     # 现网 config 全量关键项导出
│   ├── 03-verbose改动.diff           # 本次 config 逐行 diff
│   └── 04-macOS26升级评估与排查方案.md # 核心报告：黑屏根因 + 26 兼容性 + 升级路线
├── scripts/
│   ├── analyze_config.py             # config.plist 关键项导出工具
│   └── patch_verbose.py              # -v/调试开关补丁脚本（可复现）
├── tools/                            # OC 0.9.1/1.0.7、ProperTree（二进制不入库，见 tools/README.md）
└── upstream/                         # 上游仓库与 3.3.0/4.0.0 Release（不入库）
```

## 当前状态（2026-08-30）

- 现网：macOS 13.7.8 + OpenCore 0.9.1（上游 2023-05-15 版），运行正常。
- 已完成：EFI 完整备份入库；硬件清单；与上游逐文件对比；**已把开机改为 verbose 跑码 + panic/OC 日志落盘并部署**。
- 结论：现 EFI 直接升 macOS 26 必黑屏（同 15 的根因：OC/kext 落后 3 年）；硬件本身兼容 Tahoe，需先把 OC 升到 1.0.7、kext 全量换新。详见 `docs/04`。

## 紧急回滚（恢复 logo 开机）

```bash
sudo diskutil mount disk0s1
# 用 EFI 内就地备份覆盖回去：
cp /Volumes/Untitled/EFI/OC/config.plist.bak-before-verbose /Volumes/Untitled/EFI/OC/config.plist
sudo diskutil unmount disk0s1
```

## Git 提交约定

每次修改一次 commit：备份基线 → 文档/分析 → 工作副本 → 部署记录，可逐阶段回溯。
