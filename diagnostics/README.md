# diagnostics/ 日志回传区

- `opencore/`   ← ESP 根的 opencore-YYYY-MM-DD-*.txt（保留原文件名）
- `panic/`      ← `nvram -x aapl,panic-info` 导出 + /Library/Logs/DiagnosticReports 拷贝
- `sysdiagnose/`← sysdiagnose 包 / log show / ioreg / kextstat / pmset
- `photos/`     ← 跑码或 panic 屏照片，命名 <阶段>_<时间>.jpg
- `findings.md` ← 每轮诊断追加一节（模板已写好）

规范详见仓库 `docs/08-外部诊断Agent交接手册.md` §7–§8。诊断完成后整个目录拷回仓库 `docs/forensics/` 归档。
