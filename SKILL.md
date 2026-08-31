---
name: photo-illustration-diptych
description: "Turn one uploaded real-person photo into a finished side-by-side image: a subject-aware 3:4 crop of the original on the left and a matching 3:4 fixed-style signed illustration on the right. Use for 照片转插画、原图与插画左右拼接、3:4 双联图；不要用于普通修图或只生成单张插画的请求。"
---

# 照片转插画拼接

## 成品标准

生成一张横向双联图：

- 左侧：用户原照片经人物感知的 3:4 裁切，不重绘、不调换内容。
- 右侧：以左侧裁切图为唯一内容与构图依据生成的 3:4 固定风格插画。
- 两侧尺寸一致，默认各为 768×1024；无缝拼接后为 1536×1024（3:2）。
- 插画背景为 `#FDFCFC` 轻纸纹；亚洲人物的裸露皮肤统一为 `#FFF1DF`。
- 插画带一个手写签名。用户未提交签名时，固定使用 `XRWRX`。

## 输入与默认值

- 必需：一张真实照片。
- 可选：签名文字或透明签名图片。缺失时直接使用默认签名，不要为此追问。
- 固定素材位于 `assets/style-board.png`、`assets/series-anchor-working.png`、`assets/series-anchor-reading.png`、`assets/series-anchor-cigrette.png` 和 `assets/color-spec.png`。每次最多选择两个最贴近当前照片动作的系列锚点。
- 默认输出只保留最终拼接图；若用户需要，再额外交付裁切照片或带签名插画。

## 工作流

1. 阅读 [references/illustration-prompt.md](references/illustration-prompt.md)。
2. 查看上传照片，识别主要人物、姿态和必须保留的随身物品。主体只包括人物、穿戴物，以及人物正在手持或直接使用的关键物品。
3. 确定归一化裁切焦点 `focus-x`、`focus-y`（范围 0～1），确保脸、手、脚和关键物品优先保留。使用 `scripts/prepare_photo.py` 输出 3:4 左图。不要直接拿未裁切原图生成插画。
4. 使用内置图片生成工具制作右图。最多使用五张输入：裁切照片、风格板、从 `series-anchor-working.png`、`series-anchor-reading.png`、`series-anchor-cigrette.png` 中选择的两个最相关系列锚点，以及颜色规范图。把裁切照片标为唯一编辑目标；风格板和系列锚点仅限风格参考；颜色规范图的上半部分代表背景 `#FDFCFC`，下半部分代表亚洲人物肤色 `#FFF1DF`，不得把色块形状画进成品。使用参考提示词，并根据照片内容填入人物、服装、动作和关键物品。生成阶段不要让模型写签名或其他文字；签名在后处理中确定性添加，以避免错字。为签名保留不遮挡主体的空白区域。
5. 检查右图：人物数量、身份线索、姿态、双手与物品关系、3:4 比例、背景清理、肤色统一和画风必须通过。亚洲人物还要运行 `scripts/validate_illustration.py --expect-asian-skin`。一次只针对一个明确问题重试。
6. 使用 `scripts/compose_diptych.py` 给右图添加签名并左右拼接。签名位置自动从右下、右上、左下、左上中选择最空的位置；颜色自动取插画中的深灰或黑色。
7. 用图片查看工具检查最终成品，确认左右没有拉伸、签名准确、没有额外文字或背景杂物，再交付最终路径和预览。

## 命令

先通过工作区依赖加载器取得带 Pillow 和 NumPy 的 Python 路径，然后运行：

```bash
<python> scripts/prepare_photo.py \
  --input <原照片> \
  --output <3x4裁切照片.png> \
  --focus-x 0.50 \
  --focus-y 0.50
```

生成插画后运行：

```bash
<python> scripts/compose_diptych.py \
  --photo <3x4裁切照片.png> \
  --illustration <无签名插画.png> \
  --output <最终拼接图.png> \
  --signature-text "XRWRX"
```

亚洲人物先校验无签名右图：

```bash
<python> scripts/validate_illustration.py \
  --image <无签名插画.png> \
  --expect-asian-skin
```

用户提供透明签名图片时，使用 `--signature-image <路径>`。用户提供其他签名文字时，将 `--signature-text` 替换为该文字。不要同时让模型生成签名并再次叠加签名。

## 不可变约束

- 左图必须是原照片的裁切，不能被模型重绘。
- 右图必须基于左图而不是未裁切原图，避免左右构图失配。
- 删除插画主体外的一切环境内容；不得补充参考图中的古装、动物、道具或场景。
- 背景纸纹只能轻微、均匀、干净；不得做旧、泛黄、斑驳或出现落地影。
- 亚洲人物的脸、耳朵、脖子、手和其他裸露皮肤必须使用同一 `#FFF1DF` 基底色。
- 最终画面只允许一个签名。除签名外不得出现文字、Logo、水印或边框。
- 默认签名必须准确为 `XRWRX`，不得改字、漏字或添加空格。
