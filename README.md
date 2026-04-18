# MDBlogPacker

发博客的效率工具：把 Markdown 里的本地图片批量转换成 Base64 内嵌格式，自动复制到剪贴板，粘贴到博客园、CSDN、掘金等支持 Base64 图片的平台就能直接发布 —— 不用再一张一张传图床。

> 💡 **Obsidian 用户**：我还做了同功能的 Obsidian 插件版，右键笔记就能一键转换 → [MDImageEmbed](https://github.com/MZSH-ObsidianPlugins/MDImageEmbed)

## 为什么需要这个工具

发博客时最烦的就是图片 —— 本地图片没法直接发布，传图床又要一张张上传、复制链接、替换路径。Base64 内嵌把所有图片打进 Markdown 文本里，复制就能发。

## 功能

- 扫描 Markdown 里所有本地图片（支持 `![](path)` 和 Obsidian `![[image.png]]` 两种语法）
- 自动转换为 `data:image/...;base64,...` 内嵌格式
- 结果直接复制到剪贴板，粘贴即发
- 支持前缀/后缀模板文件（版权声明、防转载提示等）
- 网络图片和已是 Base64 的保持不动

## 使用

```bash
# 最常用：转换 + 复制到剪贴板
python Main.py 博客.md -c

# 带版权前后缀
python Main.py 博客.md -c -p 前缀.md -s 后缀.md

# 输出到文件（不走剪贴板）
python Main.py 博客.md -o 博客-内嵌版.md

# 查看详细转换日志
python Main.py 博客.md -c -v
```

## 安装

```bash
pip install -r requirements.txt
```

## 参数

| 参数 | 说明 |
|---|---|
| `input` | 输入 Markdown 文件路径（必填） |
| `-c / --clipboard` | 复制到剪贴板（主要用法） |
| `-o / --output` | 输出到文件 |
| `-p / --prefix` | 前缀模板文件，拼到正文开头 |
| `-s / --suffix` | 后缀模板文件，拼到正文结尾 |
| `--no-wiki-links` | 不转换 Obsidian `![[]]` Wiki 链接 |
| `--no-skip-base64` | 不跳过已是 Base64 的图片 |
| `-v / --verbose` | 详细日志（列出每张图的处理状态） |

不指定 `-c` 和 `-o` 时默认输出到标准输出，可用管道。

## 图片路径解析规则

按顺序尝试：

1. 绝对路径
2. 相对源 MD 文件所在目录
3. Obsidian vault 根相对路径（如 `/附件/xxx.png`，自动向上查找 `.obsidian/` 目录定位 vault 根）

支持 URL 编码字符（`%20` 等）自动解码。

## 支持的图片格式

PNG、JPG、JPEG、GIF、WebP、SVG、BMP

## 注意事项

- Base64 会让文件体积增加约 33%，图太多或太大时慎用
- 网络图片（`http://` / `https://`）会保持原状不转换
- 建议只在"导出发布"时用，日常写作仍保留独立图片文件便于维护

## 许可证

MIT License
