---
type: dashboard
status: active
updated: 2026-07-27
---

# 知识库仪表盘

## 进行中的项目

```dataview
TABLE status AS 状态, deadline AS 截止, file.mtime AS 最近更新
FROM "10-Projects"
WHERE type = "project" AND status = "active"
SORT file.mtime DESC
```

## 全库未完成任务

```tasks
not done
sort by due
sort by priority
group by folder
```

## 最近沉淀的知识

```dataview
LIST
FROM "40-Knowledge"
WHERE status = "evergreen"
SORT file.mtime DESC
LIMIT 10
```

## 最近 7 天更新

```dataview
TABLE file.folder AS 目录, file.mtime AS 更新时间
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
LIMIT 20
```
