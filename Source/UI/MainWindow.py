"""MDBlogPacker 主窗口：选 MD + 填前文/后文 → 转换并复制到剪贴板"""
import sys
from pathlib import Path

import pyperclip


def _GetExeDir() -> Path:
    """获取可执行文件所在目录（兼容 PyInstaller 打包与源码运行）"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent
from PySide2 import QtCore, QtWidgets

from Source.Logic.ConfigManager import ConfigManager
from Source.Logic.Converter import ConvertMarkdown


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.Config = ConfigManager()
        self.setWindowTitle("MDBlogPacker")
        self.resize(720, 560)
        self._BuildUi()
        self._LoadFromConfig()

    def _BuildUi(self):
        Layout = QtWidgets.QVBoxLayout(self)

        # MD 文件选择
        FileRow = QtWidgets.QHBoxLayout()
        FileRow.addWidget(QtWidgets.QLabel("MD 文件："))
        self.FilePathEdit = QtWidgets.QLineEdit()
        self.FilePathEdit.setPlaceholderText("选择或粘贴本地 Markdown 文件路径")
        FileRow.addWidget(self.FilePathEdit, 1)
        BtnBrowse = QtWidgets.QPushButton("浏览…")
        BtnBrowse.clicked.connect(self._OnBrowse)
        FileRow.addWidget(BtnBrowse)
        Layout.addLayout(FileRow)

        # 前文输入
        Layout.addWidget(QtWidgets.QLabel("前文（拼到正文开头，可留空）："))
        self.PrefixEdit = QtWidgets.QPlainTextEdit()
        self.PrefixEdit.setPlaceholderText("例如：版权声明、转载提示…")
        Layout.addWidget(self.PrefixEdit, 1)

        # 后文输入
        Layout.addWidget(QtWidgets.QLabel("后文（拼到正文结尾，可留空）："))
        self.SuffixEdit = QtWidgets.QPlainTextEdit()
        self.SuffixEdit.setPlaceholderText("例如：作者介绍、关注引导…")
        Layout.addWidget(self.SuffixEdit, 1)

        # 转换按钮
        self.BtnConvert = QtWidgets.QPushButton("转换并复制到剪贴板")
        self.BtnConvert.setMinimumHeight(40)
        self.BtnConvert.clicked.connect(self._OnConvert)
        Layout.addWidget(self.BtnConvert)

        # 状态栏
        self.StatusLabel = QtWidgets.QLabel("就绪")
        self.StatusLabel.setStyleSheet("color: gray;")
        Layout.addWidget(self.StatusLabel)

    def _LoadFromConfig(self):
        MdFiles = sorted(_GetExeDir().glob("*.md"))
        if MdFiles:
            self.FilePathEdit.setText(str(MdFiles[0]))
        self.PrefixEdit.setPlainText(self.Config.Get("Prefix", ""))
        self.SuffixEdit.setPlainText(self.Config.Get("Suffix", ""))

    def _SaveToConfig(self):
        self.Config.Set("Prefix", self.PrefixEdit.toPlainText())
        self.Config.Set("Suffix", self.SuffixEdit.toPlainText())
        self.Config.Save()

    def _OnBrowse(self):
        # 起始目录优先级：输入框里已有路径的父目录 → exe 所在目录
        StartDir = str(_GetExeDir())
        CurPath = self.FilePathEdit.text().strip()
        if CurPath:
            CurParent = Path(CurPath).parent
            if CurParent.is_dir():
                StartDir = str(CurParent)

        FilePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择 Markdown 文件", StartDir, "Markdown (*.md);;所有文件 (*)"
        )
        if FilePath:
            self.FilePathEdit.setText(FilePath)

    def _OnConvert(self):
        MdPath = self.FilePathEdit.text().strip()
        if not MdPath:
            self._SetStatus("❌ 请先选择 MD 文件", IsError=True)
            return

        MdFile = Path(MdPath)
        if not MdFile.is_file():
            self._SetStatus(f"❌ 文件不存在: {MdPath}", IsError=True)
            return

        try:
            Content = MdFile.read_text(encoding="utf-8")
        except Exception as E:
            self._SetStatus(f"❌ 读取失败: {E}", IsError=True)
            return

        PrefixText = self.PrefixEdit.toPlainText().strip()
        SuffixText = self.SuffixEdit.toPlainText().strip()

        if PrefixText:
            Content = PrefixText + "\n\n" + Content
        if SuffixText:
            Content = Content + "\n\n" + SuffixText

        try:
            Result, ConvertedCnt, SkippedCnt, _ = ConvertMarkdown(
                Content,
                SourceDir=MdFile.parent,
                ConvertWikiLinks=True,
                SkipBase64=True,
                Verbose=False,
            )
        except Exception as E:
            self._SetStatus(f"❌ 转换失败: {E}", IsError=True)
            return

        try:
            pyperclip.copy(Result)
        except Exception as E:
            self._SetStatus(f"❌ 复制剪贴板失败: {E}", IsError=True)
            return

        self._SaveToConfig()
        self._SetStatus(f"✅ 已复制到剪贴板（转换 {ConvertedCnt}，跳过 {SkippedCnt}）")

    def _SetStatus(self, Text: str, IsError: bool = False):
        self.StatusLabel.setText(Text)
        Color = "#c0392b" if IsError else "#27ae60"
        self.StatusLabel.setStyleSheet(f"color: {Color};")

    def closeEvent(self, Event: QtCore.QEvent):
        self._SaveToConfig()
        super().closeEvent(Event)
