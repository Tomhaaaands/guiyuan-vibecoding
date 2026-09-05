---
artifact_id: technical/migration/audit
kind: technical-spec
status: accepted
supports: [product/install]
---
# Migration Audit And Adoption

`tools/architecture_audit.py` 只读检测旧目录、根目录权威文档和缺失层；迁移必须先记录基线，
再按 `keep`、`map`、`managed` 执行，哈希校验和备份后才允许写入。

## 完全接管迁移

完全接管不是一次无条件复制。流程固定为：

1. 评估阶段统计排除依赖/缓存后的文件体量，并盘点候选数据；
2. 用户确认模板、规模和能力后，在项目目录之外生成 `--migration-plan`；
3. 只有再次传入 `--migration-confirm`，且评估、数据摘要、模板和文本引用哈希均未变化时才执行；
4. 数据目录按明确映射可逆移动，未知目录保留原位；明确的文本路径引用先备份再替换；
5. 管理层、模板布局和旧管理层归档完成后写入 `.guiyuan-vibecoding/takeover.json`。

目标已存在、引用文件发生变化或执行中出现异常时，流程停止并按迁移回执逆序恢复。业务代码
默认不迁移、不覆盖；`--migrate-code` 也只允许用户显式选择的已知代码根别名。
