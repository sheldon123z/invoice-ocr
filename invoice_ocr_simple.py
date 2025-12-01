#!/usr/bin/env python3
"""
极简发票 OCR 汇总工具 - 仅识别金额（修复版 - 支持长文件名）

特点：
- 快速扫描并提取发票金额
- 递归扫描当前目录下的 PDF/图片发票
- PDF 首页转 PNG 后识别
- 调用 Ollama 提取总金额，并统计合计
- ✅ 支持长文件名和中文命名
- ✅ 自动跳过含有"行程单"的文件
- ✅ 自动验证发票，跳过非发票文件

使用：
  python3 invoice_ocr_simple_v2.py              # 扫描当前目录
  python3 invoice_ocr_simple_v2.py /path/to/dir  # 扫描指定目录
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


# 简化的识别提示词 - 只关注金额
SIMPLE_PROMPT = (
    "你是发票识别专家。仔细识别图片中发票的价税合计金额。\n"
    "仅返回JSON格式：{\"total\": 数值}\n"
    "金额必须准确，仅数字，如1234.56\n"
    "无法识别时返回 {\"total\": 0}\n"
    "不要输出其他任何内容。"
)

VALIDATE_PROMPT = (
    "请判断图片中的文件是否是发票。\n"
    "如果是发票（增值税发票、普通发票等），返回 {\"is_invoice\": true}\n"
    "如果不是发票（行程单、收据等），返回 {\"is_invoice\": false}\n"
    "不要输出其他任何内容。"
)

OLLAMA_HOST = "192.168.110.219"
OLLAMA_PORT = 11434
OLLAMA_MODEL = "qwen3-vl:8b"

# 统一 OCR Provider（由 GUI 设置）
OCR_PROVIDER = None


def run_pdftoppm_first_page(pdf_path: Path, tmpdir: Path) -> Path:
    """将 PDF 第一页转换成 PNG（支持长文件名）。"""
    # 使用短标识符避免路径过长
    short_id = hashlib.md5(str(pdf_path).encode()).hexdigest()[:8]
    output_prefix = tmpdir / short_id

    cmd = [
        "pdftoppm",
        "-png",
        "-singlefile",
        "-f", "1",
        "-l", "1",
        str(pdf_path),
        str(output_prefix),
    ]
    proc = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        error_msg = proc.stderr.decode('utf-8', 'ignore').strip()
        raise RuntimeError(f"pdftoppm 失败: {error_msg}")

    out_png = output_prefix.with_suffix(".png")
    if not out_png.exists():
        raise FileNotFoundError(f"pdftoppm 未生成输出文件（可能是PDF格式问题）")
    return out_png


def call_ollama_ocr(image_path: Path, prompt: str, timeout: int = 300) -> str:
    """调用 OCR（支持统一 Provider 或 Ollama）"""
    # 优先使用统一 Provider
    if OCR_PROVIDER is not None:
        try:
            return OCR_PROVIDER.call_ocr(image_path, prompt, timeout)
        except Exception as e:
            raise RuntimeError(f"OCR API 调用失败: {e}")
    
    # 回退到原有 Ollama 调用
    with image_path.open("rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("ascii")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        "stream": False,
    }
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")
    except Exception as e:
        raise RuntimeError(f"Ollama 调用失败: {e}")


def parse_amount(response_text: str) -> float:
    """解析金额，简单快速。"""
    try:
        data = json.loads(response_text)
        if isinstance(data, dict) and "total" in data:
            val = data["total"]
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                return float(val.replace(",", "").strip() or 0)
    except Exception:
        pass

    # 回退：正则抓取最大数字
    nums = []
    for match in re.findall(r"[-+]?\d+(?:[.,]\d+)?", response_text):
        try:
            nums.append(float(match.replace(",", "")))
        except ValueError:
            continue
    return max(nums) if nums else 0.0


def validate_is_invoice(image_path: Path) -> bool:
    """验证文件是否是发票（可选，避免处理非发票文件）。"""
    try:
        response = call_ollama_ocr(image_path, VALIDATE_PROMPT, timeout=60)
        data = json.loads(response)
        return data.get("is_invoice", False)
    except Exception:
        # 验证失败时假定为发票，继续处理
        return True


def iter_invoice_files(root: Path) -> Iterable[Path]:
    """递归扫描发票文件（跳过行程单和非发票文件）。"""
    exts = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    skip_keywords = {"行程单", "itinerary", "receipt"}  # 跳过的关键词

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            # 跳过含有特定关键词的文件
            if any(keyword in path.name.lower() for keyword in skip_keywords):
                continue
            yield path


def process_file(path: Path) -> Tuple[float, str]:
    """处理单个文件，返回金额和状态。"""
    try:
        # 获取处理用的图片路径
        image_path = path
        temp_png = None

        if path.suffix.lower() == ".pdf":
            with tempfile.TemporaryDirectory(prefix="inv_") as tmp:
                try:
                    temp_png = run_pdftoppm_first_page(path, Path(tmp))
                    image_path = temp_png

                    # 验证是否为发票
                    if not validate_is_invoice(image_path):
                        return 0.0, "⊘ 非发票"

                    response = call_ollama_ocr(image_path, SIMPLE_PROMPT)
                    amount = parse_amount(response)
                    return amount, "✓" if amount > 0 else "⚠"
                except Exception as e:
                    return 0.0, f"✗ PDF处理失败"
        else:
            # 验证是否为发票
            if not validate_is_invoice(image_path):
                return 0.0, "⊘ 非发票"

            response = call_ollama_ocr(image_path, SIMPLE_PROMPT)
            amount = parse_amount(response)
            return amount, "✓" if amount > 0 else "⚠"
    except (HTTPError, URLError) as e:
        return 0.0, "⚠ 网络错误"
    except Exception as e:
        return 0.0, f"✗ 错误"


def main() -> int:
    parser = argparse.ArgumentParser(description="极简发票 OCR 汇总 - 快速识别金额（支持长文件名）")
    parser.add_argument("root", nargs="?", default=".", help="扫描目录（默认当前目录）")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[错误] 路径不存在: {root}", file=sys.stderr)
        return 1

    files = list(iter_invoice_files(root))
    if not files:
        print(f"[提示] 未找到发票文件")
        return 0

    print(f"共发现 {len(files)} 份发票，开始识别...\n")

    grand_total = 0.0
    success_count = 0
    non_invoice_count = 0
    results: List[Tuple[Path, float, str]] = []

    for idx, path in enumerate(files, 1):
        amount, status = process_file(path)
        if "非发票" in status:
            non_invoice_count += 1
        grand_total += amount
        if amount > 0:
            success_count += 1
        print(f"[{idx:03d}] {path.name:<50} {amount:>10.2f} 元  {status}")
        results.append((path, amount, status))

    # 输出汇总
    print("\n" + "=" * 80)
    print(f"发票总数：{len(results)}")
    print(f"成功识别：{success_count}")
    if non_invoice_count > 0:
        print(f"非发票文件：{non_invoice_count}")
    print(f"总金额：{grand_total:.2f} 元")
    print("=" * 80)

    # 输出 Markdown
    output_file = root / "invoice_summary.md"
    lines = [
        "# 发票 OCR 汇总",
        f"- 扫描目录：`{root}`",
        f"- 发票数量：{len(results)}",
        f"- 成功识别：{success_count}",
        f"- **总金额：{grand_total:.2f} 元**",
        "",
        "## 明细",
        "| 序号 | 文件 | 金额(元) | 状态 |",
        "| --- | --- | --- | --- |",
    ]
    for i, (path, amount, status) in enumerate(results, 1):
        rel = path.relative_to(root)
        lines.append(f"| {i} | `{rel.name}` | {amount:.2f} | {status} |")

    try:
        output_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n✅ 报告已保存: {output_file}")
    except Exception as e:
        print(f"\n❌ 保存失败: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
