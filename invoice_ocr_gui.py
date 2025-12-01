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
    ollama_host: str = "192.168.110.219"
    ollama_port: int = 11434
    ollama_model: str = "qwen3-vl:8b"
    max_retries: int = 3
    scan_directory: str = ""
    mode: str = "simple"  # simple 或 full
    enable_excel: bool = True
    enable_rename: bool = False
    enable_validate: bool = True


class InvoiceOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("发票 OCR 识别工具")
        self.root.geometry("900x700")
        
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
            options_check_frame, text="验证发票", 
            variable=self.validate_var
        )
        validate_check.pack(side=tk.LEFT, padx=10)
        
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
            "1. 设置 Ollama 服务器地址和端口\n"
            "2. 选择要使用的视觉模型（如 qwen3-vl:8b）\n"
            "3. 配置处理选项和重试次数\n"
            "4. 点击\"测试连接\"确保服务器可访问\n"
            "5. 返回\"处理发票\"标签开始识别\n\n"
            "💡 提示：\n"
            "- 快速模式：仅识别发票金额，速度快\n"
            "- 完整模式：提取完整信息，支持统计分析\n"
            "- 配置会自动保存到本地文件"
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
        self.config.enable_rename = self.rename_var.get()
        self.config.enable_validate = self.validate_var.get()
        
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
        
    def process_invoices(self):
        """处理发票（在后台线程中运行）"""
        try:
            root = Path(self.config.scan_directory)
            
            # 检查连接
            self.message_queue.put(("log", f"🌐 服务器: {self.config.ollama_host}:{self.config.ollama_port}"))
            self.message_queue.put(("log", f"🤖 模型: {self.config.ollama_model}"))
            self.message_queue.put(("log", ""))
            
            # 导入必要的模块并设置参数
            if self.config.mode == "simple":
                from invoice_ocr_simple import (
                    SIMPLE_PROMPT, iter_invoice_files, 
                    process_file as process_simple
                )
                # 更新全局配置
                import invoice_ocr_simple
                invoice_ocr_simple.OLLAMA_HOST = self.config.ollama_host
                invoice_ocr_simple.OLLAMA_PORT = self.config.ollama_port
                invoice_ocr_simple.OLLAMA_MODEL = self.config.ollama_model
            else:
                from invoice_ocr_sum import (
                    iter_invoice_files, process_file,
                    validate_and_analyze, generate_excel_report,
                    rename_invoice_files
                )
                # 更新全局配置
                import invoice_ocr_sum
                invoice_ocr_sum.OLLAMA_HOST = self.config.ollama_host
                invoice_ocr_sum.OLLAMA_PORT = self.config.ollama_port
                invoice_ocr_sum.OLLAMA_MODEL = self.config.ollama_model
            
            # 扫描文件
            files = list(iter_invoice_files(root))
            if not files:
                self.message_queue.put(("log", "❌ 未找到发票文件"))
                self.message_queue.put(("done", None))
                return
                
            self.message_queue.put(("log", f"✅ 发现 {len(files)} 份发票文件"))
            self.message_queue.put(("log", f"🔧 模式: {self.config.mode}"))
            self.message_queue.put(("log", f"🌐 服务器: {self.config.ollama_host}:{self.config.ollama_port}"))
            self.message_queue.put(("log", f"🤖 模型: {self.config.ollama_model}\n"))
            
            if self.config.mode == "simple":
                # 简单模式
                grand_total = 0.0
                success_count = 0
                
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
                        
                    msg = f"[{idx:03d}/{len(files)}] {path.name[:40]:<40} {amount:>10.2f} 元  {status}"
                    self.message_queue.put(("log", msg))
                    
                self.message_queue.put(("log", "\n" + "=" * 80))
                self.message_queue.put(("log", f"📊 处理完成"))
                self.message_queue.put(("log", f"  发票总数：{len(files)}"))
                self.message_queue.put(("log", f"  成功识别：{success_count}"))
                self.message_queue.put(("log", f"  💰 总金额：{grand_total:.2f} 元"))
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
                        self.prompt = invoice_ocr_sum.DEFAULT_PROMPT
                        
                args = Args(self.config)
                
                for idx, path in enumerate(files, 1):
                    if not self.processing:
                        break
                        
                    self.message_queue.put((
                        "progress", 
                        (idx / len(files)) * 100
                    ))
                    
                    info, errors = process_file(path, args, max_retries=self.config.max_retries)
                    status = "✓ OK" if not errors else f"⚠ {errors[0][:30]}"
                    
                    msg = f"[{idx:03d}/{len(files)}] {path.name[:40]:<40} {info.total:>10.2f} 元  {status}"
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
            self.config.ollama_host = self.host_var.get()
            self.config.ollama_port = int(self.port_var.get())
            self.config.ollama_model = self.model_var.get()
            self.config.max_retries = int(self.retry_var.get())
            
            self.save_config()
            messagebox.showinfo("成功", "设置已保存")
        except ValueError:
            messagebox.showerror("错误", "端口和重试次数必须是数字")
            
    def reset_settings(self):
        """恢复默认设置"""
        self.config = AppConfig()
        self.host_var.set(self.config.ollama_host)
        self.port_var.set(str(self.config.ollama_port))
        self.model_var.set(self.config.ollama_model)
        self.retry_var.set(str(self.config.max_retries))
        messagebox.showinfo("成功", "已恢复默认设置")
        
    def test_connection(self):
        """测试 Ollama 连接"""
        try:
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
                    messagebox.showinfo(
                        "连接成功", 
                        f"✅ 已连接到 Ollama 服务器\n\n可用模型：\n" + "\n".join(models[:10])
                    )
                else:
                    messagebox.showwarning("连接成功", "服务器已连接，但未找到模型")
                    
        except Exception as e:
            error_msg = f"❌ 无法连接到服务器:\n\n错误信息:\n{e}\n\n可能的原因：\n"
            
            if "No route to host" in str(e) or "Errno 65" in str(e):
                error_msg += (
                    "1. 服务器地址不正确或服务器未启动\n"
                    "2. 防火墙阻止了连接\n"
                    "3. 设备不在同一网络\n\n"
                    "解决方法：\n"
                    "• 检查 Ollama 服务器是否运行\n"
                    "• 确认服务器地址和端口正确\n"
                    "• 检查防火墙设置"
                )
            elif "timed out" in str(e) or "timeout" in str(e).lower():
                error_msg += (
                    "1. 服务器响应过慢\n"
                    "2. 网络不稳定\n\n"
                    "解决方法：\n"
                    "• 检查网络连接\n"
                    "• 稍后重试"
                )
            elif "Connection refused" in str(e) or "Errno 61" in str(e):
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
