# AGENT_README · 黑苹果 Tahoe 安装/诊断 U 盘（先读我）

2026-08-30 交接 · 安装器 macOS Tahoe 26.6.2 (build 25G83) · 仓库快照 commit b835038

## 你是谁、要做什么

外部诊断 Agent：用本 U 盘在这台七彩虹 B460I 黑苹果上完成/修复 macOS 26 全新安装，并采集跑码日志回传。

## 三步上手

1. 先读总纲：`hackintosh-b460i-mac26/docs/08-外部诊断Agent交接手册.md`（红线 / S0–S8 跑码判定树 / 取证命令 / 回传规范）
2. 安装操作全文：`docs/07-全新安装macOS26完整步骤.md`；改 config 必须先过 `tools/oc-1.0.7/Utilities/ocvalidate/ocvalidate`（零问题才许部署），且先 git commit 再部署
3. 日志写回卷根 `diagnostics/`（结构见 docs/08 §8，模板已放 `diagnostics/findings.md`）

## 关键事实（30 秒版）

- 开机 **F11** → 选 **UEFI: U盘** → OpenCore 1.0.7 图形选择器
- **先用新 OC 引导现网 13 验证引导链，验证通过才允许抹盘**
- 抹盘只许抹 **1TB disk0**（内含 824.7GB 用户数据卷，抹前必须机主本人确认）；**12TB disk2 严禁动**
- U 盘 ESP 已部署 Tahoe EFI（同源 `efi-new/tahoe-oc107/EFI`）；调试全开：`-v`（屏幕跑码）、`debug=0x100`（panic 不自动重启）、`ApplePanic`（panic 进 NVRAM `aapl,panic-info`）、`Target=67`（OC 日志落 **ESP 根** `opencore-*.txt`）
- WiFi：itlwm 已随 EFI 加载，**连接需装卷根 HeliPort-v1.5.0.dmg**；音频限制/OTA/WEG 风险预案见 docs/06

## 卷内容

```
/Volumes/Install macOS Tahoe/
├── (macOS 安装器文件 —— 勿动)
├── AGENT_README.md            ← 本文件
├── HeliPort-v1.5.0.dmg        ← WiFi 连接工具
├── hackintosh-b460i-mac26/    ← 完整 git 仓库（含全部提交历史 / docs / tools / efi-backup）
└── diagnostics/               ← 你的日志回传区
```

## 回滚底牌

- 现网 13 未抹前任何失败 → 拔 U 盘即回 13
- 13 的 EFI 原档在仓库 `efi-backup/original-20260830/`；verbose 前正常 config 在内置盘 `config.plist.bak-before-verbose`
