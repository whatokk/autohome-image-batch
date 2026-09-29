# 汽车图片批量生成

基于参考图批量生成「真实车主随手拍」风格的车辆图（文生图 / 图生图），用于口碑与内容投放。

## 技能清单

| 技能 | 说明 |
|---|---|
| **autohome-image-batch** · 批量出图流水线 | 覆盖车型识别、参考图规格化、提示词文件 TAB 格式、中转站多通道降级排错、质检与打包交付。 |

## 安装

把 `skills/` 下的技能目录拷贝到 WorkBuddy 的技能目录：

```bash
cp -r skills/* ~/.workbuddy/skills/
```

Windows PowerShell：

```powershell
Copy-Item .\skills\* "$env:USERPROFILE\.workbuddy\skills\" -Recurse -Force
```

重启 WorkBuddy 后，技能列表即可看到。

## 使用要点

- 触发词：改提示词出图、批量生成汽车图片、按参考图生成 N 张不同视角、跑 prompts-*.txt、再出一批车主随手拍。
- 项目根 = 含 `batch.mjs` 的目录。

## 环境依赖

- Node 22
- 图片生成通道（中转站多通道）

## 目录规范

```
autohome-image-batch/
└── skills/
    ├── autohome-image-batch/
```

每个技能遵循统一结构：`SKILL.md`（必需，含 name/description frontmatter）+ `scripts/`（可选）+ `references/`（可选）。

---

## License

MIT — 随意取用、修改、二次分发。
