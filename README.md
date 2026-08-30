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
├── efi-new/
│   ├── tahoe-oc107/EFI/              # ★ macOS26 全新 EFI：OC 1.0.7 + 18 最新 kext（交付物，已入库）
│   └── companion/HeliPort-v1.5.0.dmg # ★ AX200 WiFi 连接工具（进系统后安装）
├── docs/
│   ├── 02-config-原始配置全量.txt     # 现网 config 全量关键项导出
│   ├── 03-verbose改动.diff           # 本次 config 逐行 diff
│   ├── 04-macOS26升级评估与排查方案.md # 核心报告：黑屏根因 + 26 兼容性 + 升级路线
│   ├── 05-tahoe新config全量.txt       # 全新 OC1.0.7 config 全量关键项导出
│   └── 06-Tahoe全新EFI说明.md         # ★ 新 EFI 组件/参数/WiFi/音频/风险/升级步骤
├── scripts/
│   ├── analyze_config.py             # config.plist 关键项导出工具
│   ├── patch_verbose.py              # -v/调试开关补丁脚本（可复现）
│   ├── build_new_efi.sh              # 组装 Tahoe 全新 EFI 文件树（可复现）
│   └── build_tahoe_config.py         # 生成 1.0.7 schema config（可复现）
├── tools/                            # OC 0.9.1/1.0.7、ProperTree（二进制不入库，见 tools/README.md）
└── upstream/                         # 上游仓库与 3.3.0/4.0.0 Release（不入库）
```

## 当前状态（2026-08-30）

- 现网：macOS 13.7.8 + OpenCore 0.9.1（上游 2023-05-15 版，已开 verbose 跑码），运行正常。
- 已完成：EFI 完整备份入库；硬件清单；与上游逐文件对比；现网 EFI 改 verbose 跑码并部署。
- **已交付 Tahoe 全新 EFI**：`efi-new/tahoe-oc107/EFI`（OC 1.0.7 + 18 个最新 kext，-v/ApplePanic/Target67/SecureBootModel Disabled，ocvalidate 1.0.7 零问题），仅入库**未部署**；WiFi 用 itlwm+HeliPort（HeliPort 已在当前系统装好验证）。详见 `docs/06`。
- 结论：硬件本身兼容 Tahoe；旧 EFI 直接升必黑屏（OC/kext 落后），新 EFI 即为解决方案。升级前务必先 U 盘验证（docs/06 §8）。

## 紧急回滚（恢复 logo 开机）

```bash
sudo diskutil mount disk0s1
# 用 EFI 内就地备份覆盖回去：
cp /Volumes/Untitled/EFI/OC/config.plist.bak-before-verbose /Volumes/Untitled/EFI/OC/config.plist
sudo diskutil unmount disk0s1
```

## Git 提交约定

每次修改一次 commit：备份基线 → 文档/分析 → 工作副本 → 部署记录，可逐阶段回溯。
