#!/usr/bin/env python3
"""
发票 OCR 图形界面应用程序
支持简单模式和完整模式，可自定义 Ollama 参数
"""

import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import threading
import json
from dataclasses import dataclass, asdict
from typing import Optional
import queue

# 统一 OCR 提供商
from ocr_api import create_provider

# 导入原有的 OCR 模块
try:
    from invoice_ocr_sum import (
        iter_invoice_files, process_file, validate_and_analyze,
        generate_excel_report, rename_invoice_files, InvoiceInfo
    )
    HAS_FULL_VERSION = True
except ImportError:
    HAS_FULL_VERSION = False

try:
    from invoice_ocr_simple import (
        iter_invoice_files as iter_files_simple,
        process_file as process_file_simple
    )
    HAS_SIMPLE_VERSION = True
except ImportError:
    HAS_SIMPLE_VERSION = False


@dataclass
class AppConfig:
    """应用配置"""
    # API 配置
    provider: str = "ollama"  # ollama | volcengine | openrouter
    ollama_host: str = "192.168.110.219"
    ollama_port: int = 11434
    ollama_model: str = "qwen3-vl:8b"
    volcengine_api_key: str = ""
    volcengine_model: str = ""  # 火山引擎接入点 ID（如 ep-xxx）
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"

    # 其他配置
    max_retries: int = 3
    scan_directory: str = ""
    mode: str = "simple"  # simple 或 full
    enable_excel: bool = True
    enable_markdown: bool = True
    enable_rename: bool = False
    enable_validate: bool = False  # 默认关闭以提升快速模式速度

    # 新增功能配置
    enable_verify: bool = False  # 发票真伪验证
    enable_classify: bool = False  # 发票分类

    # 自定义提示词（用于定制化报告内容或特殊要求）
    custom_prompt: str = ""


class InvoiceOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("发票 OCR 识别工具")
        # 增大界面尺寸以提供更好的用户体验
        self.root.geometry("1200x900")
        
        # 加载配置
        self.config = self.load_config()
        
        # 处理队列（用于线程间通信）
        self.message_queue = queue.Queue()
        self.processing = False
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息队列检查
        self.check_message_queue()
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标签页1: 处理发票
        self.tab_process = ttk.Frame(notebook)
        notebook.add(self.tab_process, text="📋 处理发票")
        
        # 标签页2: 设置
        self.tab_settings = ttk.Frame(notebook)
        notebook.add(self.tab_settings, text="⚙️ 设置")
        
        # 创建处理页面
        self.create_process_tab()
        
        # 创建设置页面
        self.create_settings_tab()
        
    def create_process_tab(self):
        """创建处理发票标签页"""
        frame = self.tab_process
        
        # 目录选择
        dir_frame = ttk.LabelFrame(frame, text="选择目录", padding=10)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.dir_var = tk.StringVar(value=self.config.scan_directory or str(Path.home()))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=60)
        dir_entry.pack(side=tk.LEFT, padx=5)
        
        dir_btn = ttk.Button(dir_frame, text="浏览...", command=self.select_directory)
        dir_btn.pack(side=tk.LEFT)
        
        # 处理模式和选项
        options_frame = ttk.LabelFrame(frame, text="处理选项", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 模式选择
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="处理模式:").pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value=self.config.mode)
        simple_radio = ttk.Radiobutton(
            mode_frame, text="🚀 快速模式（仅识别金额）", 
            variable=self.mode_var, value="simple"
        )
        simple_radio.pack(side=tk.LEFT, padx=10)
        
        full_radio = ttk.Radiobutton(
            mode_frame, text="📊 完整模式（详细分析）", 
            variable=self.mode_var, value="full"
        )
        full_radio.pack(side=tk.LEFT, padx=10)
        
        # 其他选项
        options_check_frame = ttk.Frame(options_frame)
        options_check_frame.pack(fill=tk.X, pady=5)
        
        self.excel_var = tk.BooleanVar(value=self.config.enable_excel)
        excel_check = ttk.Checkbutton(
            options_check_frame, text="生成 Excel 报告", 
            variable=self.excel_var
        )
        excel_check.pack(side=tk.LEFT, padx=10)
        
        self.rename_var = tk.BooleanVar(value=self.config.enable_rename)
        rename_check = ttk.Checkbutton(
            options_check_frame, text="文件重命名", 
            variable=self.rename_var
        )
        rename_check.pack(side=tk.LEFT, padx=10)
        
        self.validate_var = tk.BooleanVar(value=self.config.enable_validate)
        validate_check = ttk.Checkbutton(
            options_check_frame, text="验证发票 (⚡快速模式下建议关闭)", 
            variable=self.validate_var
        )
        validate_check.pack(side=tk.LEFT, padx=10)

        self.markdown_var = tk.BooleanVar(value=self.config.enable_markdown)
        markdown_check = ttk.Checkbutton(
            options_check_frame, text="生成 Markdown 报告", 
            variable=self.markdown_var
        )
        markdown_check.pack(side=tk.LEFT, padx=10)
        
        # 新增功能选项（第二行）
        options_check_frame2 = ttk.Frame(options_frame)
        options_check_frame2.pack(fill=tk.X, pady=5)
        
        self.verify_var = tk.BooleanVar(value=self.config.enable_verify)
        verify_check = ttk.Checkbutton(
            options_check_frame2, text="🔍 发票真伪验证", 
            variable=self.verify_var
        )
        verify_check.pack(side=tk.LEFT, padx=10)
        
        self.classify_var = tk.BooleanVar(value=self.config.enable_classify)
        classify_check = ttk.Checkbutton(
            options_check_frame2, text="🏷️ 发票分类", 
            variable=self.classify_var
        )
        classify_check.pack(side=tk.LEFT, padx=10)
        
        # 功能说明标签
        ttk.Label(options_check_frame2, text="(完整模式生效)", foreground="gray").pack(side=tk.LEFT, padx=5)

        # 自定义提示词区域
        custom_prompt_frame = ttk.LabelFrame(frame, text="🎯 自定义要求（可选）", padding=10)
        custom_prompt_frame.pack(fill=tk.X, padx=10, pady=5)

        custom_prompt_desc = ttk.Label(
            custom_prompt_frame,
            text="在此输入额外的要求，将会附加到识别提示词中。例如：\"请特别注意提取备注信息\" 或 \"需要识别公司全称\"",
            foreground="gray",
            wraplength=800
        )
        custom_prompt_desc.pack(fill=tk.X, pady=(0, 5))

        self.custom_prompt_var = tk.StringVar(value=self.config.custom_prompt)
        self.custom_prompt_entry = ttk.Entry(
            custom_prompt_frame,
            textvariable=self.custom_prompt_var,
            width=80
        )
        self.custom_prompt_entry.pack(fill=tk.X, pady=2)

        # 开始按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(
            btn_frame, text="🚀 开始处理", 
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            btn_frame, text="⏹ 停止",
            command=self.stop_processing,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            btn_frame, text="🗑 清除日志",
            command=self.clear_log
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame, variable=self.progress_var, 
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # 输出日志
        log_frame = ttk.LabelFrame(frame, text="处理日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=20, 
            font=("Courier", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def create_settings_tab(self):
        """创建设置标签页"""
        frame = self.tab_settings
        
        # API 提供商设置
        provider_frame = ttk.LabelFrame(frame, text="API 提供商", padding=15)
        provider_frame.pack(fill=tk.X, padx=10, pady=10)

        provider_row = ttk.Frame(provider_frame)
        provider_row.pack(fill=tk.X, pady=5)
        ttk.Label(provider_row, text="提供商:", width=15).pack(side=tk.LEFT)
        self.provider_var = tk.StringVar(value=self.config.provider)
        provider_combo = ttk.Combobox(provider_row, textvariable=self.provider_var, values=("ollama","volcengine","openrouter"), state="readonly", width=20)
        provider_combo.pack(side=tk.LEFT, padx=5)

        # Ollama 服务器设置
        server_frame = ttk.LabelFrame(frame, text="Ollama 服务器设置", padding=15)
        server_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 主机地址
        host_frame = ttk.Frame(server_frame)
        host_frame.pack(fill=tk.X, pady=5)
        ttk.Label(host_frame, text="服务器地址:", width=15).pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value=self.config.ollama_host)
        host_entry = ttk.Entry(host_frame, textvariable=self.host_var, width=40)
        host_entry.pack(side=tk.LEFT, padx=5)
        
        # 端口
        port_frame = ttk.Frame(server_frame)
        port_frame.pack(fill=tk.X, pady=5)
        ttk.Label(port_frame, text="端口:", width=15).pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(self.config.ollama_port))
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=40)
        port_entry.pack(side=tk.LEFT, padx=5)
        
        # 模型
        model_frame = ttk.Frame(server_frame)
        model_frame.pack(fill=tk.X, pady=5)
        ttk.Label(model_frame, text="模型:", width=15).pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=self.config.ollama_model)
        model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=40)
        model_entry.pack(side=tk.LEFT, padx=5)

        # 火山引擎设置
        volc_frame = ttk.LabelFrame(frame, text="火山引擎 (Volcengine)", padding=15)
        volc_frame.pack(fill=tk.X, padx=10, pady=10)
        volc_row1 = ttk.Frame(volc_frame); volc_row1.pack(fill=tk.X, pady=5)
        ttk.Label(volc_row1, text="API Key:", width=15).pack(side=tk.LEFT)
        self.volc_api_key_var = tk.StringVar(value=self.config.volcengine_api_key)
        ttk.Entry(volc_row1, textvariable=self.volc_api_key_var, width=40, show="*").pack(side=tk.LEFT, padx=5)
        volc_row2 = ttk.Frame(volc_frame); volc_row2.pack(fill=tk.X, pady=5)
        ttk.Label(volc_row2, text="接入点 ID:", width=15).pack(side=tk.LEFT)
        self.volc_model_var = tk.StringVar(value=self.config.volcengine_model)
        ttk.Entry(volc_row2, textvariable=self.volc_model_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Label(volc_row2, text="(如 ep-xxx)", foreground="gray").pack(side=tk.LEFT, padx=5)

        # OpenRouter 设置
        or_frame = ttk.LabelFrame(frame, text="OpenRouter", padding=15)
        or_frame.pack(fill=tk.X, padx=10, pady=10)
        or_row1 = ttk.Frame(or_frame); or_row1.pack(fill=tk.X, pady=5)
        ttk.Label(or_row1, text="API Key:", width=15).pack(side=tk.LEFT)
        self.or_api_key_var = tk.StringVar(value=self.config.openrouter_api_key)
        ttk.Entry(or_row1, textvariable=self.or_api_key_var, width=40, show="*").pack(side=tk.LEFT, padx=5)
        
        or_row2 = ttk.Frame(or_frame); or_row2.pack(fill=tk.X, pady=5)
        ttk.Label(or_row2, text="Model:", width=15).pack(side=tk.LEFT)
        self.or_model_var = tk.StringVar(value=self.config.openrouter_model)
        # 使用Combobox替代Entry
        self.or_model_combo = ttk.Combobox(or_row2, textvariable=self.or_model_var, width=37, state="normal")
        self.or_model_combo.pack(side=tk.LEFT, padx=5)
        # 初始化为当前值，后续可以刷新
        self.or_model_combo['values'] = [self.config.openrouter_model]
        
        # 添加刷新按钮
        refresh_btn = ttk.Button(or_row2, text="🔄 刷新模型", command=self.refresh_openrouter_models, width=12)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 高级设置
        advanced_frame = ttk.LabelFrame(frame, text="高级设置", padding=15)
        advanced_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 重试次数
        retry_frame = ttk.Frame(advanced_frame)
        retry_frame.pack(fill=tk.X, pady=5)
        ttk.Label(retry_frame, text="最大重试次数:", width=15).pack(side=tk.LEFT)
        self.retry_var = tk.StringVar(value=str(self.config.max_retries))
        retry_spinbox = ttk.Spinbox(
            retry_frame, from_=0, to=10, 
            textvariable=self.retry_var, width=10
        )
        retry_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=20)
        
        save_btn = ttk.Button(
            btn_frame, text="💾 保存设置", 
            command=self.save_settings
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = ttk.Button(
            btn_frame, text="🔄 恢复默认", 
            command=self.reset_settings
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # 测试连接按钮
        test_btn = ttk.Button(
            btn_frame, text="🔌 测试连接", 
            command=self.test_connection
        )
        test_btn.pack(side=tk.LEFT, padx=5)
        
        # 说明文本
        info_frame = ttk.LabelFrame(frame, text="说明", padding=15)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = (
            "📌 使用说明：\n\n"
            "1. 选择 API 提供商：Ollama / 火山引擎 / OpenRouter\n"
            "2. 根据所选提供商配置相应参数：\n"
            "   - Ollama: 设置服务器地址、端口和模型名\n"
            "   - 火山引擎: 设置 API Key 和 Endpoint ID（从控制台获取）\n"
            "   - OpenRouter: 设置 API Key 和模型名（支持 400+ 模型）\n"
            "3. 点击\"测试连接\"验证配置\n"
            "4. 返回\"处理发票\"标签开始识别\n\n"
            "💡 模式选择：\n"
            "- 快速模式：仅识别发票金额，速度快\n"
            "  ⚡ 建议关闭\"验证发票\"选项以获得最佳性能\n"
            "- 完整模式：提取完整信息，支持统计分析\n\n"
            "💾 配置会自动保存到 ~/.invoice_ocr_config.json"
        )
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
    def select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(
            initialdir=self.dir_var.get(),
            title="选择发票目录"
        )
        if directory:
            self.dir_var.set(directory)
            
    def log(self, message):
        """输出日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_processing(self):
        """开始处理"""
        if self.processing:
            return
            
        directory = self.dir_var.get()
        if not directory or not Path(directory).exists():
            messagebox.showerror("错误", "请选择有效的目录")
            return
            
        # 更新配置
        self.config.scan_directory = directory
        self.config.mode = self.mode_var.get()
        self.config.enable_excel = self.excel_var.get()
        self.config.enable_markdown = self.markdown_var.get()
        self.config.enable_rename = self.rename_var.get()
        self.config.enable_validate = self.validate_var.get()
        # 新增功能配置
        self.config.enable_verify = self.verify_var.get()
        self.config.enable_classify = self.classify_var.get()
        # 自定义提示词
        self.config.custom_prompt = self.custom_prompt_var.get().strip()
        # API 提供商
        self.config.provider = self.provider_var.get()
        self.config.ollama_host = self.host_var.get()
        self.config.ollama_port = int(self.port_var.get())
        self.config.ollama_model = self.model_var.get()
        self.config.volcengine_api_key = self.volc_api_key_var.get()
        self.config.volcengine_model = self.volc_model_var.get()
        self.config.openrouter_api_key = self.or_api_key_var.get()
        self.config.openrouter_model = self.or_model_var.get()
        
        # 更新界面状态
        self.processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_invoices, daemon=True)
        thread.start()
        
    def stop_processing(self):
        """停止处理"""
        self.processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("⏹ 处理已停止")

    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)

    def process_invoices(self):
        """处理发票（在后台线程中运行）"""
        try:
            root = Path(self.config.scan_directory)
            
            # 显示当前配置
            provider_name = {
                "ollama": "Ollama",
                "volcengine": "火山引擎",
                "openrouter": "OpenRouter"
            }.get(self.config.provider, self.config.provider)
            
            self.message_queue.put(("log", f"🔌 API 提供商: {provider_name}"))
            
            if self.config.provider == "ollama":
                self.message_queue.put(("log", f"🌐 服务器: {self.config.ollama_host}:{self.config.ollama_port}"))
                self.message_queue.put(("log", f"🤖 模型: {self.config.ollama_model}"))
            elif self.config.provider == "volcengine":
                self.message_queue.put(("log", f"🔑 Endpoint ID: {self.config.volcengine_model}"))
            elif self.config.provider == "openrouter":
                self.message_queue.put(("log", f"🤖 模型: {self.config.openrouter_model}"))
            
            self.message_queue.put(("log", ""))
            
            # 创建 OCR 提供商
            provider = create_provider(asdict(self.config))

            # 导入必要的模块并设置参数
            if self.config.mode == "simple":
                from invoice_ocr_simple import (
                    SIMPLE_PROMPT, iter_invoice_files,
                    process_file as process_simple
                )
                # 更新全局配置
                import invoice_ocr_simple
                # 兼容原有参数（Ollama 回退用）
                invoice_ocr_simple.OLLAMA_HOST = self.config.ollama_host
                invoice_ocr_simple.OLLAMA_PORT = self.config.ollama_port
                invoice_ocr_simple.OLLAMA_MODEL = self.config.ollama_model
                # 设置统一 Provider
                invoice_ocr_simple.OCR_PROVIDER = provider
                # 设置自定义提示词
                invoice_ocr_simple.CUSTOM_PROMPT = self.config.custom_prompt
                # 设置是否启用验证（快速模式下默认关闭以提升速度）
                invoice_ocr_simple.ENABLE_VALIDATION = self.config.enable_validate
            else:
                from invoice_ocr_sum import (
                    iter_invoice_files, process_file,
                    validate_and_analyze, generate_excel_report,
                    rename_invoice_files, verify_invoice, classify_invoice
                )
                # 更新全局配置
                import invoice_ocr_sum
                # 兼容原有参数（Ollama 回退用）
                invoice_ocr_sum.OLLAMA_HOST = self.config.ollama_host
                invoice_ocr_sum.OLLAMA_PORT = self.config.ollama_port
                invoice_ocr_sum.OLLAMA_MODEL = self.config.ollama_model
                # 设置统一 Provider
                invoice_ocr_sum.OCR_PROVIDER = provider
            
            # 扫描文件
            files = list(iter_invoice_files(root))
            if not files:
                self.message_queue.put(("log", "❌ 未找到发票文件"))
                self.message_queue.put(("done", None))
                return
                
            self.message_queue.put(("log", f"✅ 发现 {len(files)} 份发票文件"))
            self.message_queue.put(("log", f"🔧 模式: {'简单' if self.config.mode == 'simple' else '完整'}\n"))
            
            if self.config.mode == "simple":
                # 简单模式
                grand_total = 0.0
                success_count = 0
                results = []  # 保存处理结果用于报告

                # 显示自定义提示词信息
                if self.config.custom_prompt:
                    self.message_queue.put(("log", f"📝 自定义要求：{self.config.custom_prompt[:50]}{'...' if len(self.config.custom_prompt) > 50 else ''}"))
                    self.message_queue.put(("log", ""))

                for idx, path in enumerate(files, 1):
                    if not self.processing:
                        break

                    self.message_queue.put((
                        "progress",
                        (idx / len(files)) * 100
                    ))

                    amount, status = process_simple(path)
                    grand_total += amount
                    if amount > 0:
                        success_count += 1

                    results.append((path, amount, status))

                    msg = f"[{idx:03d}/{len(files)}] {path.name[:40]:<40} {amount:>10.2f} 元  {status}"
                    self.message_queue.put(("log", msg))

                self.message_queue.put(("log", "\n" + "=" * 80))
                self.message_queue.put(("log", f"📊 处理完成"))
                self.message_queue.put(("log", f"  发票总数：{len(files)}"))
                self.message_queue.put(("log", f"  成功识别：{success_count}"))
                self.message_queue.put(("log", f"  💰 总金额：{grand_total:.2f} 元"))
                # 生成 Markdown 报告（快速模式）
                if self.config.enable_markdown:
                    try:
                        output_md = root / "invoice_summary.md"
                        from datetime import datetime
                        lines = [
                            "# 📋 发票 OCR 汇总报告 (快速模式)",
                            "",
                            f"- 🗂️ 扫描目录：`{root}`",
                            f"- 📊 发票数量：{len(files)} 份",
                            f"- ✅ 成功识别：{success_count} 份",
                            f"- 💰 总金额：**{grand_total:.2f} 元**",
                            "",
                            "## 📝 明细表",
                            "",
                            "| 序号 | 文件 | 金额(元) | 状态 |",
                            "| :---: | --- | ---: | --- |",
                        ]
                        # 使用保存的处理结果生成明细
                        for i, (path, amount, status) in enumerate(results, 1):
                            lines.append(f"| {i} | `{path.name}` | {amount:.2f} | {status} |")
                        lines.append("")
                        lines.append("---")
                        lines.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                        output_md.write_text("\n".join(lines), encoding="utf-8")
                        self.message_queue.put(("log", f"\n✅ Markdown 报告: {output_md}"))
                    except Exception as e:
                        self.message_queue.put(("log", f"\n⚠️ Markdown 导出失败: {e}"))
                self.message_queue.put(("log", "=" * 80))
                
            else:
                # 完整模式
                invoices = []

                # 创建参数对象
                class Args:
                    def __init__(self, config):
                        self.host = config.ollama_host
                        self.port = config.ollama_port
                        self.model = config.ollama_model
                        # 构建提示词：默认提示词 + 自定义提示词
                        base_prompt = invoice_ocr_sum.DEFAULT_PROMPT
                        if config.custom_prompt:
                            self.prompt = f"{base_prompt}\n\n【用户额外要求】\n{config.custom_prompt}"
                        else:
                            self.prompt = base_prompt

                args = Args(self.config)

                # 显示自定义提示词信息
                if self.config.custom_prompt:
                    self.message_queue.put(("log", f"📝 自定义要求：{self.config.custom_prompt[:50]}..."))
                
                for idx, path in enumerate(files, 1):
                    if not self.processing:
                        break
                        
                    self.message_queue.put((
                        "progress", 
                        (idx / len(files)) * 100
                    ))
                    
                    info, errors = process_file(path, args, max_retries=self.config.max_retries)
                    
                    # 发票验证功能（可选）
                    if self.config.enable_verify and info.total > 0:
                        try:
                            import tempfile
                            if path.suffix.lower() == ".pdf":
                                # PDF需要转换为图片
                                with tempfile.TemporaryDirectory(prefix="inv_verify_") as tmp:
                                    from invoice_ocr_sum import run_pdftoppm_first_page
                                    png_path = run_pdftoppm_first_page(path, Path(tmp))
                                    verify_result = verify_invoice(png_path, args)
                            else:
                                verify_result = verify_invoice(path, args)
                            
                            info.risk_level = verify_result.get("risk_level", "low")
                            info.risk_notes = verify_result.get("risk_notes", "")
                            info.has_stamp = verify_result.get("has_stamp", True)
                            info.image_quality = verify_result.get("image_quality", "good")
                        except Exception as e:
                            info.risk_notes = f"验证失败: {str(e)[:30]}"
                    
                    # 发票分类功能（可选）
                    if self.config.enable_classify and info.total > 0:
                        try:
                            import tempfile
                            if path.suffix.lower() == ".pdf":
                                with tempfile.TemporaryDirectory(prefix="inv_class_") as tmp:
                                    from invoice_ocr_sum import run_pdftoppm_first_page
                                    png_path = run_pdftoppm_first_page(path, Path(tmp))
                                    class_result = classify_invoice(png_path, args)
                            else:
                                class_result = classify_invoice(path, args)
                            
                            info.invoice_type = class_result.get("invoice_type", "other")
                            info.invoice_type_name = class_result.get("invoice_type_name", "其他类型")
                            info.expense_category = class_result.get("expense_category", "other")
                            info.expense_category_name = class_result.get("expense_category_name", "其他")
                        except Exception:
                            pass
                    
                    status = "✓ OK" if not errors else f"⚠ {errors[0][:30]}"
                    
                    # 添加风险等级标记
                    risk_mark = ""
                    if info.risk_level == "high":
                        risk_mark = " ⚠️高风险"
                    elif info.risk_level == "medium":
                        risk_mark = " ❓中风险"
                    
                    msg = f"[{idx:03d}/{len(files)}] {path.name[:40]:<40} {info.total:>10.2f} 元  {status}{risk_mark}"
                    self.message_queue.put(("log", msg))
                    invoices.append((path, info, errors))
                    
                # 分析和报告
                self.message_queue.put(("log", "\n" + "=" * 80))
                analysis = validate_and_analyze(invoices)
                
                self.message_queue.put(("log", "📊 统计汇总"))
                self.message_queue.put(("log", f"  发票总数：{analysis['total_count']}"))
                self.message_queue.put(("log", f"  有效发票：{analysis['valid_count']}"))
                self.message_queue.put(("log", f"  💰 总金额：{analysis['total_amount']:.2f} 元"))
                self.message_queue.put(("log", f"  平均金额：{analysis['total_amount'] / max(analysis['total_count'], 1):.2f} 元"))
                
                # 生成报告
                if self.config.enable_excel:
                    try:
                        output_xlsx = root / "invoice_summary.xlsx"
                        if generate_excel_report(invoices, analysis, output_xlsx):
                            self.message_queue.put(("log", f"\n✅ Excel 报告: {output_xlsx}"))
                    except Exception as e:
                        self.message_queue.put(("log", f"\n⚠️ Excel 导出失败: {e}"))

                # 生成 Markdown 报告（完整模式）
                if self.config.enable_markdown:
                    try:
                        output_md = root / "invoice_summary.md"
                        lines = [
                            "# 📋 发票 OCR 汇总报告 (完整模式)",
                            "",
                            f"- 🗂️ 扫描目录：`{root}`",
                            f"- 📊 发票总数：{analysis['total_count']} 份",
                            f"- ✅ 有效发票：{analysis['valid_count']} 份",
                            f"- 💰 总金额：**{analysis['total_amount']:.2f} 元**",
                            "",
                            "## 📝 发票明细",
                            "",
                            "| 序号 | 文件名 | 发票类型 | 发票号码 | 金额(元) | 开票日期 | 状态 |",
                            "| :---: | --- | --- | --- | ---: | --- | --- |",
                        ]
                        for i, (path, info, errors) in enumerate(invoices, 1):
                            status = "✓" if not errors else f"⚠ {errors[0][:20]}" if errors else "✓"
                            invoice_type = info.invoice_type_name or "-"
                            invoice_no = info.invoice_no or "-"
                            invoice_date = info.issue_date or "-"
                            lines.append(
                                f"| {i} | `{path.name}` | {invoice_type} | {invoice_no} | {info.total:.2f} | {invoice_date} | {status} |"
                            )
                        lines.append("")
                        lines.append("---")
                        from datetime import datetime
                        lines.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                        output_md.write_text("\n".join(lines), encoding="utf-8")
                        self.message_queue.put(("log", f"✅ Markdown 报告: {output_md}"))
                    except Exception as e:
                        self.message_queue.put(("log", f"⚠️ Markdown 导出失败: {e}"))

                # 文件重命名
                if self.config.enable_rename:
                    rename_ops = rename_invoice_files(invoices, rename=True)
                    renamed_count = sum(1 for op in rename_ops if op.startswith('✓'))
                    self.message_queue.put(("log", f"\n✅ 已重命名 {renamed_count} 份文件"))
                    
                self.message_queue.put(("log", "=" * 80))
                
            self.message_queue.put(("done", None))
            
        except Exception as e:
            self.message_queue.put(("log", f"\n❌ 错误: {e}"))
            self.message_queue.put(("done", None))
            
    def check_message_queue(self):
        """检查消息队列"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                
                if msg_type == "log":
                    self.log(msg_data)
                elif msg_type == "progress":
                    self.progress_var.set(msg_data)
                elif msg_type == "done":
                    self.processing = False
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    self.progress_var.set(100)
                    
        except queue.Empty:
            pass
            
        # 继续检查
        self.root.after(100, self.check_message_queue)
        
    def save_settings(self):
        """保存设置"""
        try:
            self.config.provider = self.provider_var.get()
            self.config.ollama_host = self.host_var.get()
            self.config.ollama_port = int(self.port_var.get())
            self.config.ollama_model = self.model_var.get()
            self.config.volcengine_api_key = self.volc_api_key_var.get()
            self.config.volcengine_model = self.volc_model_var.get()
            self.config.openrouter_api_key = self.or_api_key_var.get()
            self.config.openrouter_model = self.or_model_var.get()
            self.config.max_retries = int(self.retry_var.get())

            self.save_config()
            messagebox.showinfo("成功", "设置已保存")
        except ValueError:
            messagebox.showerror("错误", "端口和重试次数必须是数字")
            
    def reset_settings(self):
        """恢复默认设置"""
        self.config = AppConfig()
        self.provider_var.set(self.config.provider)
        self.host_var.set(self.config.ollama_host)
        self.port_var.set(str(self.config.ollama_port))
        self.model_var.set(self.config.ollama_model)
        self.volc_api_key_var.set(self.config.volcengine_api_key)
        self.volc_model_var.set(self.config.volcengine_model)
        self.or_api_key_var.set(self.config.openrouter_api_key)
        self.or_model_var.set(self.config.openrouter_model)
        self.retry_var.set(str(self.config.max_retries))
        messagebox.showinfo("成功", "已恢复默认设置")
        
    def refresh_openrouter_models(self):
        """刷新OpenRouter模型列表"""
        api_key = self.or_api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请先输入 OpenRouter API Key")
            return
        
        try:
            # 显示加载中
            self.or_model_combo.config(state="disabled")
            self.root.config(cursor="watch")
            self.root.update()
            
            # 从 ocr_api 导入 OpenRouterProvider
            from ocr_api import OpenRouterProvider
            models = OpenRouterProvider.fetch_models(api_key, timeout=15)
            
            if not models:
                messagebox.showinfo("提示", "未找到可用模型")
                return
            
            # 更新下拉框
            model_ids = [model_id for model_id, _ in models]
            self.or_model_combo['values'] = model_ids
            
            # 如果当前值不在列表中，设置为第一个
            current_model = self.or_model_var.get()
            if current_model not in model_ids and model_ids:
                self.or_model_var.set(model_ids[0])
            
            messagebox.showinfo("成功", f"✅ 已加载 {len(models)} 个模型")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新模型列表失败:\n{str(e)}")
        finally:
            # 恢复界面
            self.or_model_combo.config(state="normal")
            self.root.config(cursor="")
    
    def test_connection(self):
        """测试连接"""
        try:
            provider = self.provider_var.get()
            if provider == 'ollama':
                import urllib.request
                import json
                host = self.host_var.get()
                port = self.port_var.get()
                url = f"http://{host}:{port}/api/tags"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    models = [m.get('name', '') for m in data.get('models', [])]
                    if models:
                        messagebox.showinfo("连接成功", f"✅ 已连接到 Ollama 服务器\n\n可用模型：\n" + "\n".join(models[:10]))
                    else:
                        messagebox.showwarning("连接成功", "服务器已连接，但未找到模型")
            elif provider == 'volcengine':
                ok = bool(self.volc_api_key_var.get())
                if ok:
                    messagebox.showinfo("检查完成", "✅ 已检测到火山引擎 API Key（未实际调用）")
                else:
                    messagebox.showwarning("检查失败", "请填写火山引擎 API Key")
            else:
                ok = bool(self.or_api_key_var.get())
                if ok:
                    messagebox.showinfo("检查完成", "✅ 已检测到 OpenRouter API Key（未实际调用）")
                else:
                    messagebox.showwarning("检查失败", "请填写 OpenRouter API Key")
        except Exception as e:
            error_str = str(e)
            error_msg = f"❌ 无法连接到服务器:\n{e}\n\n可能原因：\n"

            if "No route to host" in error_str or "Errno 65" in error_str:
                error_msg += (
                    "1. 服务器地址不正确或服务器未启动\n"
                    "2. 防火墙阻止了连接\n"
                    "3. 设备不在同一网络\n\n"
                    "解决方法：\n"
                    "• 检查 Ollama 服务器是否运行\n"
                    "• 确认服务器地址和端口正确\n"
                    "• 检查防火墙设置"
                )
            elif "timed out" in error_str or "timeout" in error_str.lower():
                error_msg += (
                    "1. 服务器响应过慢\n"
                    "2. 网络不稳定\n\n"
                    "解决方法：\n"
                    "• 检查网络连接\n"
                    "• 稍后重试"
                )
            elif "Connection refused" in error_str or "Errno 61" in error_str:
                error_msg += (
                    "1. Ollama 服务未运行\n"
                    "2. 端口不正确\n\n"
                    "解决方法：\n"
                    "• 在服务器上启动 Ollama\n"
                    "• 确认端口设置正确（默认 11434）"
                )
            else:
                error_msg += (
                    "1. 服务器设置错误\n"
                    "2. 网络连接问题\n\n"
                    "解决方法：\n"
                    "• 检查服务器地址和端口\n"
                    "• 确保 Ollama 服务运行中"
                )

            messagebox.showerror("连接失败", error_msg)
            
    def load_config(self) -> AppConfig:
        """加载配置"""
        config_file = Path.home() / ".invoice_ocr_config.json"
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AppConfig(**data)
        except Exception:
            pass
        return AppConfig()
        
    def save_config(self):
        """保存配置"""
        config_file = Path.home() / ".invoice_ocr_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")


def main():
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('default')
    
    app = InvoiceOCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
