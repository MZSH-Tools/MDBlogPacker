# MDBlogPacker

将 Markdown 里的本地图片批量转换为 Base64 内嵌格式，输出为自包含的单文件 Markdown —— 便于博客发布、跨平台分享、脱离图床依赖。

源自 [MDImageEmbed Obsidian 插件](https://github.com/MZSH-ObsidianPlugins/MDImageEmbed) 的 Python CLI 版本，脱离 Obsidian 环境可用。

## 特性

- 扫描 `![alt](path)` 和 Obsidian `![[image.png]]` 两种图片语法
- 本地图片自动转换为 `data:image/...;base64,...` 形式
- 跳过网络图片（http/https）和已是 Base64 的图片
- 支持前缀/后缀模板文件（防转载声明、版权信息等）
- 输出去向：标准输出 / 文件 / 剪贴板

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 输出到 stdout（可配合管道）
python Main.py blog.md

# 输出到文件
python Main.py blog.md -o blog-inline.md

# 复制到剪贴板（适合贴进微信公众号、知乎等编辑器）
python Main.py blog.md -c

# 带前缀 + 后缀（比如插入版权声明）
python Main.py blog.md -p prefix.md -s suffix.md -o out.md

# 详细日志
python Main.py blog.md -v
```

## 参数

| 参数 | 说明 |
|---|---|
| `input` | 输入 md 文件路径（必填） |
| `-o / --output` | 输出文件路径 |
| `-c / --clipboard` | 复制到剪贴板（需 pyperclip） |
| `-p / --prefix` | 前缀模板文件 |
| `-s / --suffix` | 后缀模板文件 |
| `--no-wiki-links` | 不转换 Obsidian Wiki 链接 |
| `--no-skip-base64` | 不跳过已是 Base64 的图片（默认跳过） |
| `-v / --verbose` | 详细日志 |

## 图片路径解析规则

扫描到图片引用后按顺序尝试定位：
1. 绝对路径
2. 相对于源 MD 文件所在目录的路径

两种路径都支持 `%20` 等 URL 编码字符（自动解码）。

## 支持的图片格式

PNG、JPG、JPEG、GIF、WebP、SVG、BMP

## 注意事项

- Base64 编码会使文件体积增加约 33%，不建议用于图片特别多/特别大的文档
- 网络图片（`http://` / `https://`）不会被转换，保持原状
- 建议只用于"导出发布"场景，日常写作仍保留独立图片文件

## 许可证

MIT License
