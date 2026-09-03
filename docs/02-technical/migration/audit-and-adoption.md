---
artifact_id: technical/migration/audit
kind: technical-spec
status: accepted
supports: [product/install]
---
# Migration Audit And Adoption

`tools/architecture_audit.py` 只读检测旧目录、根目录权威文档和缺失层；迁移必须先记录基线，
再按 `keep`、`map`、`managed` 执行，哈希校验和备份后才允许写入。
