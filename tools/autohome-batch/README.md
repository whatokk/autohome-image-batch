# 汽车口碑图批量出图工具

> 基于参考图批量生成「真实车主随手拍」风格车辆图的完整流水线。

给定车辆参考图 + 视角/场景清单，一次产出 10 张风格统一的独立图片，用于口碑与内容投放。

---

## 为什么需要它

汽车口碑配图有硬要求：**同一台车、多角度、真实随手拍质感、不能有 AI 味**。

手工做图既慢又难保一致。这套工具把流程固化成流水线：
参考图规格化 → 提示词模板 → 批量出图 → 质检 → 交付打包。

配套的写作口径见「汽车口碑」相关技能（`autohome-koubei-write`）。

---

## 目录约定

项目根 = 含 `batch.mjs` 的目录。

| 文件 | 作用 |
|---|---|
| `batch.mjs` | 主脚本，Node 零依赖。读提示词文件 → 调 API → 存 PNG |
| `prompts-*.txt` | 提示词，每行 `参考图路径<Tab>提示词`，多图用 `\|` 分隔，`#` 为注释 |
| `config-*.json` | `baseUrl` / `apiKey` / `model` / `size` / `quality` / `retries` / `concurrency` / `outputDir` |
| `ref/<车型>/` | 规格化后的参考图（长边 1536 / JPEG q88，约 300-600KB） |
| `output-*/` | 成品 PNG（`NNN_*.png`）+ `manifest.txt` + `failed.txt` |
| `deliver.py` | 交付：按序号套场景名 + 生成 `_总览.jpg` + 打 zip |
| `run.bat` | 一键启动（`chcp 65001` + `cd /d "%~dp0"` + `pause`） |
| `make_mask.py` | 遮罩生成（配合 `polygons.json`），用于「只换窗外」局部改图 |
| `composite_scenes.py` | 内饰合成：原图 + 车窗内场景，逐像素保留原图非玻璃区 |

---

## 标准流程

### 1. 读参考图、识别车型

**先把原图压成缩略图再读**——原图 8-12MB，直读容易爆上下文。

```python
from PIL import Image
im = Image.open('ref/raw.jpg')
im.thumbnail((1024, 1024))
im.save('tmp/thumb.jpg', quality=85)
```

必要时放大关键标识区核对：后翼子板车型字标、尾部、格栅、尾标、号牌。

### 2. 规格化参考图

```python
im.thumbnail((1536, 1536))
im.convert('RGB').save('ref/<车型>/front.jpg', quality=88, optimize=True)
```

**这一步务必做**——原图 base64 后请求体过大，接口必失败。

按角度命名，常见 6 个位：

```
ref/<车型>/front.jpg     正前
ref/<车型>/front34.jpg   左前45度
ref/<车型>/rear.jpg      正后
ref/<车型>/rear34.jpg    左后45度
ref/<车型>/side.jpg      侧面
ref/<车型>/close.jpg     局部特写
```

### 3. 写提示词（六段式）

每条挂 **2 张角度匹配的参考图**。六段结构：

| 段落 | 内容 |
|---|---|
| ① 车辆锁定 | 列明全部识别特征 + 禁止改型/拉长/压扁 + 车身颜色 |
| ② 清除活动道具 | 去掉后加贴纸，**保留**原厂标识与号牌 |
| ③ 移除原背景 | 抹掉参考图的原始环境 |
| ④ 新场景 | 具体的地点 + 时间 + 天气 |
| ⑤ 视角与拍法 | 机位高度、构图、手机直出质感 |
| ⑥ 禁止项 | 拼图/九宫格/多图合成/多车同框/车展展厅/海报感/过度精修/人物/水印 |

末尾固定加「只输出 1 张独立图片」。

**只有左侧素材时**，右视角必须写明：

> 为左侧视角的水平镜像，轮眉/踏板/把手/腰线/轮毂辐条须与参考图对应。

### 4. 校验（每次写完必做）

- 任务数 = 期望条数
- TAB 分隔符正常（**必须是真实 TAB，不能是空格或全角**）
- 所有 ref 路径存在

### 5. 跑

```bash
node batch.mjs --config config-v27.json --prompts prompts-v27.txt
```

放后台跑，设较长 timeout。

> ⚠️ **复用输出目录前必查**
>
> 断点续传只按文件名前缀 `^\d{3,}_` 判断「已完成」。换车型或换参考图后若沿用同一
> `output-*`，旧成品会让新批次**被整体跳过、一张都不出**。跑前先把旧成品移出或归档到 `_archive/`。

> ⚠️ **多批同时跑**
>
> 总并发 = 各批 `concurrency` 之和。超过 3-4 路易触发 `429 上游负载已饱和`。
> 接受重试，或把各批 `concurrency` 降到 1-2。

### 6. 质检

- 拼版总览（`deliver.py` 会自动生成）
- 放大核对关键局部：号牌、前脸、尾部、中控屏
- 确认：视角场景不重复、车身特征一致、号牌正确

### 7. 交付

```bash
python deliver.py --src output-v27 --out "V27_车主随手拍_交付" --prefix V27
```

自动完成：按序号套场景名重命名 → 生成 `_总览.jpg` → 打 zip。

多批产出就打多个交付目录，互不混淆。

> **中文名打包必须走 Python `zipfile`**，不能用 PowerShell 的 `Compress-Archive`（编码风险，中文会乱码）。
>
> 自定义场景名：`--scenes scenes.json`，格式 `{"1":"左前45度_小区停车位","2":"..."}`。

---

## 中转站 API 排错（关键经验）

### 症状

同一条提示词，这次成功、下次一直报 `400 unknown_parameter`。改提示词、换参考图顺序都没用。

### 根因

很多中转站是**多通道负载均衡**。`/images/generations` 是否接受 `image`、`response_format` 参数
**随命中的上游通道而变**。

这不是缓存问题，靠「碰运气」重试是无效的。

### 解法：三级降级（已内置）

`batch.mjs` 为每个任务准备多条策略，按兼容性从低到高逐条降级：

| 顺序 | 策略 | 说明 |
|---|---|---|
| A | `gen+image+response_format` | generations 端点带 image 和 response_format |
| B | `gen+image` | 去掉 response_format |
| C | `edits` | 官方 `/images/edits` multipart 表单，**最终兜底，实测必过** |

只有**参数类错误**才降级；网络/超时/5xx 交给外层重试。
某条策略连续被拒 4 次后，本进程内不再尝试它。

运行时会打印降级日志：

```
· 策略 [gen+image+response_format] 被通道拒绝, 降级重试
· 策略 [gen+image] 被通道拒绝, 降级重试
· 通道拒绝了前 2 条策略, 已用 [edits] 出图   ✓
```

---

## 局部改图（只换窗外场景）

内饰图需要「不改原图、只换窗外的景色」，走遮罩路线：

```bash
# 1. 编辑 polygons.json，圈出车窗玻璃区域（归一化坐标 0~1）
# 2. 生成遮罩 + 核对预览
python make_mask.py
#    → masks/*.png（给接口用）
#    → mask_preview/*.jpg（叠加预览，务必先看，确认边界正确）

# 3. 出图：提示词里挂遮罩
#    ref/cabin.jpg|mask=masks/driver.png	只把车窗外换成城市街景，车内保持不变

# 4. 合成（可选）：场景图按 cover-fit 贴回车窗
python composite_scenes.py
```

遮罩语义：**透明处可编辑，不透明处保留原像素**。
带 `mask` 的任务只走 `/images/edits`，不会降级到不支持遮罩的策略——
因为降级就意味着丢失「不改原图」的约束，宁可重试。

---

## 配置

```bash
cp config.example.json config-v27.json
```

```json
{
  "baseUrl": "https://your-api.com/v1",
  "apiKey": "",
  "model": "gpt-image-1",
  "size": "1024x1536",
  "quality": "high",
  "concurrency": 2,
  "retries": 4,
  "outputDir": "output-v27"
}
```

**密钥建议用环境变量**，不要写进文件：

```bash
export API_KEY="sk-xxxxx"          # macOS / Linux
export API_BASE_URL="https://your-api.com/v1"
setx API_KEY "sk-xxxxx"            # Windows
```

完整配置项见 `batch.mjs` 顶部 `DEFAULT_CONFIG`。

---

## 环境要求

- Node.js 18+
- Python 3.8+ 与 Pillow（`deliver.py` / `make_mask.py` / `composite_scenes.py` 需要）
- Chrome（质检时看总览图）

---

## License

MIT
