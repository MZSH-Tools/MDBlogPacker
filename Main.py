"""MDBlogPacker - 将 Markdown 的本地图片转为 Base64 内嵌，便于博客发布

入口分发：有参数走 CLI（不加载 Qt），无参数启动 GUI。
"""
import sys


def _DispatchCli() -> int:
    """CLI 模式：命令行参数处理。"""
    import argparse
    from pathlib import Path

    # Windows 控制台默认 GBK，强制切 UTF-8 以免中文/emoji 编码崩
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from Source.Logic.Converter import ConvertMarkdown, ReadTemplateFile

    Parser = argparse.ArgumentParser(
        prog="MDBlogPacker",
        description="将 Markdown 中的本地图片转换为 Base64 内嵌格式，便于博客发布",
    )
    Parser.add_argument("input", type=Path, help="输入 Markdown 文件路径")
    Parser.add_argument("-o", "--output", type=Path,
                        help="输出文件路径（默认输出到标准输出）")
    Parser.add_argument("-c", "--clipboard", action="store_true",
                        help="复制到剪贴板（与 -o 互斥）")
    Parser.add_argument("-p", "--prefix", type=Path,
                        help="前缀模板文件路径，内容会拼到正文开头")
    Parser.add_argument("-s", "--suffix", type=Path,
                        help="后缀模板文件路径，内容会拼到正文结尾")
    Parser.add_argument("--no-wiki-links", action="store_true",
                        help="不转换 Obsidian Wiki 链接 ![[image.png]]")
    Parser.add_argument("--no-skip-base64", action="store_true",
                        help="不跳过已是 Base64 的图片（默认跳过）")
    Parser.add_argument("-v", "--verbose", action="store_true",
                        help="显示详细日志")
    Args = Parser.parse_args()

    if not Args.input.is_file():
        print(f"❌ 输入文件不存在: {Args.input}", file=sys.stderr)
        return 1

    Content = Args.input.read_text(encoding="utf-8")

    if Args.prefix:
        Prefix = ReadTemplateFile(Args.prefix)
        if Prefix:
            Content = Prefix + "\n\n" + Content
        elif Args.verbose:
            print(f"⚠️ 前缀文件未找到或为空: {Args.prefix}", file=sys.stderr)
    if Args.suffix:
        Suffix = ReadTemplateFile(Args.suffix)
        if Suffix:
            Content = Content + "\n\n" + Suffix
        elif Args.verbose:
            print(f"⚠️ 后缀文件未找到或为空: {Args.suffix}", file=sys.stderr)

    Result, ConvertedCnt, SkippedCnt, _ = ConvertMarkdown(
        Content,
        SourceDir=Args.input.parent,
        ConvertWikiLinks=not Args.no_wiki_links,
        SkipBase64=not Args.no_skip_base64,
        Verbose=Args.verbose,
    )

    if Args.clipboard:
        try:
            import pyperclip
        except ImportError:
            print("❌ 剪贴板功能需要 pyperclip", file=sys.stderr)
            return 1
        pyperclip.copy(Result)
        print(f"✅ 已复制到剪贴板（转换 {ConvertedCnt}，跳过 {SkippedCnt}）",
              file=sys.stderr)
    elif Args.output:
        Args.output.parent.mkdir(parents=True, exist_ok=True)
        Args.output.write_text(Result, encoding="utf-8")
        print(f"✅ 已写入 {Args.output}（转换 {ConvertedCnt}，跳过 {SkippedCnt}）",
              file=sys.stderr)
    else:
        sys.stdout.write(Result)
        print(f"\n✅ 转换 {ConvertedCnt}，跳过 {SkippedCnt}", file=sys.stderr)
    return 0


def _DispatchGui() -> int:
    """GUI 模式：PySide2 主窗口。"""
    from PySide2 import QtWidgets
    from Source.UI.MainWindow import MainWindow

    App = QtWidgets.QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    return App.exec_()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(_DispatchCli())
    else:
        sys.exit(_DispatchGui())
