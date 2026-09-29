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

## 配套工具链

`tools/autohome-batch/` 是本技能对应的**可运行工具链**（纯 Node + Python，零外部依赖）：

| 文件 | 作用 |
|---|---|
| `batch.mjs` | 主脚本。读 `prompts-*.txt` → 调图像 API → 落 PNG，支持多通道降级与断点续传 |
| `make_mask.py` | 按 `polygons.json` 生成遮罩，用于「只改车窗/局部」重绘 |
| `composite_scenes.py` | 内饰合成：原图 + 窗内场景，逐像素保留原图非玻璃区域 |
| `modify_prompts.py` | 提示词批量改写/去重工具 |
| `deliver.py` | 交付打包：按序号套场景名 + 生成总览图 + zip |
| `run.bat` | Windows 一键启动 |
| `config.example.json` | 接口配置模板（复制为 `config.json` 后填 `baseUrl` / `apiKey`） |

**快速开始**

```bash
cd tools/autohome-batch
cp config.example.json config.json    # 填入你的接口地址与 Key
node batch.mjs                        # 或双击 run.bat
```

也可以不写配置文件，直接用环境变量：

```bash
export API_BASE_URL="https://your-api.com/v1"
export API_KEY="sk-xxxx"
node batch.mjs
```

---

## 环境依赖

- Node 22
- 图片生成通道（中转站多通道）

## 目录规范

```
autohome-image-batch/
├── skills/
│   └── autohome-image-batch/
└── tools/
    └── autohome-batch/       # 可运行的工具链
```

每个技能遵循统一结构：`SKILL.md`（必需，含 name/description frontmatter）+ `scripts/`（可选）+ `references/`（可选）。

---

## License

MIT — 随意取用、修改、二次分发。
