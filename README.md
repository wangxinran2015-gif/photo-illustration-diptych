# Photo Illustration Diptych

一个可复用的 Codex Skill：把用户上传的真实照片自动裁切为 3:4，并生成固定纸本插画风格的 3:4 右图，最后添加手写签名并左右拼接。

## 成品规则

- 左侧：原照片的人物感知 3:4 裁切，不重绘。
- 右侧：以裁切照片为构图依据的固定风格插画。
- 最终尺寸：默认 `1536×1024`，左右各 `768×1024`。
- 插画背景：`#FDFCFC`，带轻微、均匀、干净的纸纹。
- 亚洲人物裸露皮肤：统一为 `#FFF1DF`。
- 删除主体之外的环境杂物，只保留人物、穿戴物及正在手持或直接使用的关键物品。
- 默认签名：`XRWRX`；支持自定义文字或透明签名图片。

## 目录

```text
photo-illustration-diptych/
├── SKILL.md
├── agents/openai.yaml
├── assets/
├── references/illustration-prompt.md
└── scripts/
```

## 安装

将整个目录复制到 Codex skills 目录：

```bash
cp -R photo-illustration-diptych ~/.codex/skills/
```

安装脚本依赖：

```bash
python3 -m pip install -r requirements.txt
```

重新打开 Codex 后，可用类似提示调用：

```text
使用 $photo-illustration-diptych 把我上传的照片生成左侧原照、右侧签名插画的拼接图。
```

## 工作流

1. `scripts/prepare_photo.py` 生成人物感知的 3:4 原图裁切。
2. 内置图片生成工具结合风格板、动作锚点和颜色规范生成无签名插画。
3. `scripts/validate_illustration.py` 检查比例、背景与亚洲人物肤色。
4. `scripts/compose_diptych.py` 确定性添加签名并拼接最终双联图。

测试照片和生成成品位于本地 `outputs/`，已被 `.gitignore` 排除，不会上传到仓库。
