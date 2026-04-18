"""核心转换逻辑：扫描 Markdown 的图片引用并替换为 Base64 data URI"""
import base64
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import unquote


# 匹配两种图片语法：
# 1. 标准 Markdown：![alt](path) 或 ![alt](<path>)
# 2. Obsidian Wiki：![[image.png]]
ImageRegex = re.compile(
    r"!\[([^\]]*)\]\(<?([^)\">]+)>?\)"
    r"|!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp))\]\]",
    re.IGNORECASE,
)


def ReadTemplateFile(TemplatePath: Path) -> str:
    """读取前缀/后缀模板文件；不存在返回空串"""
    if not TemplatePath or not TemplatePath.is_file():
        return ""
    return TemplatePath.read_text(encoding="utf-8")


def GetMimeType(Extension: str) -> str:
    MimeMap = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
    }
    return MimeMap.get(Extension.lower(), "image/png")


def FindObsidianVaultRoot(SourceDir: Path) -> Optional[Path]:
    """从源文件目录向上查找 .obsidian/，返回 vault 根目录（找不到返回 None）"""
    Current = SourceDir.resolve()
    while True:
        if (Current / ".obsidian").is_dir():
            return Current
        Parent = Current.parent
        if Parent == Current:
            return None
        Current = Parent


def ResolveImagePath(ImagePath: str, SourceDir: Path) -> Optional[Path]:
    """按顺序尝试：绝对路径 / 相对源 MD 的路径 / Obsidian vault 根相对路径。支持 URL 解码"""
    Clean = ImagePath.strip().strip("<>")
    try:
        Clean = unquote(Clean)
    except Exception:
        pass

    # 1. 绝对路径
    AbsPath = Path(Clean)
    if AbsPath.is_absolute() and AbsPath.is_file():
        return AbsPath

    # 2. 相对源 MD 所在目录
    RelPath = (SourceDir / Clean).resolve()
    if RelPath.is_file():
        return RelPath

    # 3. Obsidian vault 根相对（如 /附件/xxx.png）
    VaultRoot = FindObsidianVaultRoot(SourceDir)
    if VaultRoot:
        Stripped = Clean.lstrip("/\\")
        VaultPath = (VaultRoot / Stripped).resolve()
        if VaultPath.is_file():
            return VaultPath

    return None


def ImageToBase64(ImagePath: str, SourceDir: Path, Verbose: bool = False) -> Optional[str]:
    ResolvedPath = ResolveImagePath(ImagePath, SourceDir)
    if not ResolvedPath:
        if Verbose:
            print(f"  └─ 未找到: {ImagePath}", file=sys.stderr)
        return None
    try:
        Data = ResolvedPath.read_bytes()
        B64 = base64.b64encode(Data).decode("ascii")
        Mime = GetMimeType(ResolvedPath.suffix)
        if Verbose:
            print(f"  └─ {ResolvedPath.name} ({len(Data)/1024:.1f} KB, {Mime})",
                  file=sys.stderr)
        return f"data:{Mime};base64,{B64}"
    except Exception as E:
        if Verbose:
            print(f"  └─ 读取失败 {ResolvedPath}: {E}", file=sys.stderr)
        return None


def ConvertMarkdown(
    Content: str,
    SourceDir: Path,
    ConvertWikiLinks: bool = True,
    SkipBase64: bool = True,
    Verbose: bool = False,
) -> Tuple[str, int, int, List[dict]]:
    """扫描并替换 Markdown 中的图片引用。
    返回：(转换后内容, 成功数, 跳过数, 明细列表)
    """
    Result = Content
    ConvertedCount = 0
    SkippedCount = 0
    Details: List[dict] = []

    Matches = list(ImageRegex.finditer(Content))
    if Verbose:
        print(f"[MDBlogPacker] 发现 {len(Matches)} 处图片引用", file=sys.stderr)

    for M in Matches:
        Full = M.group(0)

        if M.group(1) is not None:
            # 标准语法 ![alt](path)
            AltText = M.group(1)
            ImagePath = M.group(2)

            if SkipBase64 and ImagePath.startswith("data:image"):
                SkippedCount += 1
                Details.append({"path": "data:image/...", "status": "skipped",
                                "reason": "已是 Base64"})
                if Verbose:
                    print("[跳过] 已是 Base64", file=sys.stderr)
                continue

            if ImagePath.startswith("http://") or ImagePath.startswith("https://"):
                SkippedCount += 1
                Details.append({"path": ImagePath, "status": "skipped",
                                "reason": "网络图片"})
                if Verbose:
                    print(f"[跳过] 网络图片: {ImagePath}", file=sys.stderr)
                continue

            B64 = ImageToBase64(ImagePath, SourceDir, Verbose)
            if B64:
                Result = Result.replace(Full, f"![{AltText}]({B64})")
                ConvertedCount += 1
                Details.append({"path": ImagePath, "status": "success"})
            else:
                SkippedCount += 1
                Details.append({"path": ImagePath, "status": "failed",
                                "reason": "文件未找到"})

        elif M.group(3) is not None:
            # Obsidian Wiki 语法 ![[image.png]]
            ImageName = M.group(3)
            Display = f"![[{ImageName}]]"

            if not ConvertWikiLinks:
                SkippedCount += 1
                Details.append({"path": Display, "status": "skipped",
                                "reason": "Wiki 链接转换已禁用"})
                if Verbose:
                    print(f"[跳过] Wiki 链接 {Display}", file=sys.stderr)
                continue

            B64 = ImageToBase64(ImageName, SourceDir, Verbose)
            if B64:
                Result = Result.replace(Full, f"![{ImageName}]({B64})")
                ConvertedCount += 1
                Details.append({"path": Display, "status": "success"})
            else:
                SkippedCount += 1
                Details.append({"path": Display, "status": "failed",
                                "reason": "文件未找到"})

    if Verbose:
        print(f"[MDBlogPacker] 完成：{ConvertedCount} 成功 / {SkippedCount} 跳过",
              file=sys.stderr)
    return Result, ConvertedCount, SkippedCount, Details
