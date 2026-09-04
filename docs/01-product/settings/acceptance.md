# Settings Acceptance

- 用户能查看当前 Provider 和迁移确认策略。
- 修改后有明确的保存状态；失败不覆盖旧值。
- 迁移类高风险设置默认要求用户确认。
- 项目状态页可由 `python tools/render_project_home.py` 生成并直接以文件方式打开；不要求
  8010 端口监听或常驻服务。
