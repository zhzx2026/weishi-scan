# 微师课程监控

每日扫描微师(weishi100)平台新增课程，发现指定老师(classId=59253)的新课时通过邮件通知。

## 结构

```
index.html                        # 老师课程总览 (GitHub Pages 在线查看)
.github/workflows/daily-scan.yml   # 每日定时任务 (UTC 1:00 = 北京时间 9:00)
scripts/
  daily_scan.py                    # 增量扫描 [基线, 基线+500], 新课追加 CSV
  send_report.py                   # 邮件发送 (发现新课: 链接), reported.json 去重
data/
  baseline.json                    # 扫描基线 (单课/系列最大ID)
  reported.json                    # 已发邮件通知过的课程ID (不重复发)
  courses/                         # 老师数据 + 每日新增
```

## Secrets

- `WEISHI_COOKIE` / `WEISHI_UA`: 微师登录 cookie (过期后扫描会 401 并邮件告警)
- `MAIL_API_KEY`: mail.sunsetzhong.indevs.in 的 API key
- `MAIL_TO`: 收件邮箱列表 (逗号分隔)

## 手动触发

```bash
gh workflow run daily-scan.yml
```

## 邮件格式

发现新课：课程名(链接) — 单课: mweb/single/1/?id=X, 系列课: mweb/series/?id=X

## 课程总览

https://zhzx2026.github.io/weishi-scan/  (老师 645 门单课, 按系列分组, 支持搜索)
