"""
本地图片压缩程序
支持 JPG/JPEG/PNG/WEBP 格式，压缩后输出到原文件夹下的 compressed 子目录。
"""

import os
import sys

# 解决 Windows 终端中文乱码和代理字符编码问题
if sys.platform == "win32":
    os.system("")  # 启用 ANSI 转义支持
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # 确保 stdin 也使用 utf-8，支持中文路径输入
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="surrogatepass")

from pathlib import Path
from PIL import Image

# 支持的图片扩展名
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# JPG/WEBP 默认压缩质量 (1-100)
DEFAULT_QUALITY = 100

# 默认缩放比例 (0.1-1.0)，1.0 为不缩放
DEFAULT_SCALE = 0.5


def normalize_path(folder: str) -> str:
    """规范化路径：处理 MSYS/Git Bash 风格路径、中文编码、展开用户目录等。"""
    folder = folder.strip()
    # 处理 MSYS/Git Bash 路径格式: /c/xxx -> C:/xxx
    if len(folder) >= 3 and folder[0] == "/" and folder[2] == "/":
        drive = folder[1].upper()
        folder = f"{drive}:{folder[2:]}"
    folder = os.path.expanduser(folder)
    folder = os.path.abspath(folder)
    # 清理可能的代理字符 (Windows 中文路径管道传入时可能产生)
    folder = folder.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")
    return folder


def get_image_files(folder: str) -> list[Path]:
    """扫描文件夹，返回所有支持格式的图片路径列表。"""
    folder = normalize_path(folder)
    folder_path = Path(folder)
    if not folder_path.is_dir():
        print(f"错误: '{folder}' 不是一个有效的文件夹路径。")
        sys.exit(1)

    images = [
        f
        for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return images


def format_size(size_bytes: int) -> str:
    """将字节数格式化为人类可读的大小字符串。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def compress_image(
    src_path: Path,
    output_dir: Path,
    scale: float = DEFAULT_SCALE,
    quality: int = DEFAULT_QUALITY,
    fixed_width: int | None = None,
    fixed_height: int | None = None,
) -> tuple[int, int]:
    """
    压缩单张图片并保存到输出目录。
    返回 (原始大小, 压缩后大小)。

    - fixed_width: 固定宽度 (px)，高度按比例自动计算，优先级高于 scale。
    - fixed_height: 固定高度 (px)，宽度按比例自动计算，优先级高于 scale。
    - scale: 缩放比例 (0.1-1.0)，未指定固定宽高时使用。
    - quality: JPG/WEBP 压缩质量。
    - PNG: 使用有损优化 (optimize=True) 并转为 palette 模式以尽量压缩体积。
    """
    # 构造输出文件名: compressed_原名.扩展名
    output_path = output_dir / f"compressed_{src_path.name}"
    original_size = src_path.stat().st_size

    img = Image.open(src_path)

    # 优先使用固定宽/高，另一边按原图比例计算
    if fixed_width is not None:
        new_width = fixed_width
        new_height = round(img.height * (fixed_width / img.width))
        img = img.resize((new_width, new_height), Image.LANCZOS)
    elif fixed_height is not None:
        new_height = fixed_height
        new_width = round(img.width * (fixed_height / img.height))
        img = img.resize((new_width, new_height), Image.LANCZOS)
    elif scale < 1.0:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        img = img.resize((new_width, new_height), Image.LANCZOS)

    suffix = src_path.suffix.lower()

    if suffix in {".jpg", ".jpeg"}:
        # JPG: 以指定质量压缩
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=quality, optimize=True)

    elif suffix == ".webp":
        # WEBP: 以指定质量压缩
        if img.mode == "RGBA":
            img.save(output_path, "WEBP", quality=quality, method=6)
        else:
            if img.mode == "P":
                img = img.convert("RGB")
            img.save(output_path, "WEBP", quality=quality, method=6)

    elif suffix == ".png":
        # PNG: 尽量压缩体积
        if img.mode == "RGBA":
            img.save(output_path, "PNG", optimize=True, compress_level=9)
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_converted = img.quantize(method=Image.Quantize.MEDIANCUT)
            img_converted.save(output_path, "PNG", optimize=True, compress_level=9)

    compressed_size = output_path.stat().st_size

    # 如果压缩后反而更大，则用原图替换，确保不会越压越大
    if compressed_size >= original_size:
        import shutil
        shutil.copy2(src_path, output_path)
        compressed_size = original_size

    return original_size, compressed_size


def main():
    print("=" * 60)
    print("  本地图片压缩工具")
    print("  支持: JPG / JPEG / PNG / WEBP")
    print("=" * 60)

    # 用户输入文件夹路径
    folder = input("\n请输入图片文件夹路径: ").strip().strip('"').strip("'")
    folder = normalize_path(folder)

    # 选择压缩方式
    fixed_width = None
    fixed_height = None
    scale = DEFAULT_SCALE

    print("\n请选择压缩方式:")
    print("  1. 按比例缩放 (默认)")
    print("  2. 固定宽度")
    print("  3. 固定高度")
    mode_input = input("请输入选项 (1/2/3, 回车默认1): ").strip()

    if mode_input == "2":
        w_input = input("请输入目标宽度 (px): ").strip()
        if w_input.isdigit() and int(w_input) > 0:
            fixed_width = int(w_input)
        else:
            print("输入无效，将使用按比例缩放模式。")
            mode_input = "1"
    elif mode_input == "3":
        h_input = input("请输入目标高度 (px): ").strip()
        if h_input.isdigit() and int(h_input) > 0:
            fixed_height = int(h_input)
        else:
            print("输入无效，将使用按比例缩放模式。")
            mode_input = "1"

    if mode_input != "2" and mode_input != "3":
        scale_input = input(
            f"请输入缩放比例 (0.1-1.0, 回车使用默认 {DEFAULT_SCALE}): "
        ).strip()
        try:
            scale = float(scale_input)
            scale = max(0.1, min(1.0, scale))
        except ValueError:
            scale = DEFAULT_SCALE

    # 可选：自定义压缩质量
    quality_input = input(
        f"请输入 JPG/WEBP 压缩质量 (1-100, 回车使用默认 {DEFAULT_QUALITY}): "
    ).strip()
    quality = int(quality_input) if quality_input.isdigit() else DEFAULT_QUALITY
    quality = max(1, min(100, quality))

    # 扫描图片
    images = get_image_files(folder)
    if not images:
        print("\n未找到可压缩的图片文件。")
        sys.exit(0)

    dim_desc = ""
    if fixed_width is not None:
        dim_desc = f"固定宽度: {fixed_width}px"
    elif fixed_height is not None:
        dim_desc = f"固定高度: {fixed_height}px"
    else:
        dim_desc = f"缩放: {scale*100:.0f}%"
    print(f"\n找到 {len(images)} 张图片，开始压缩... ({dim_desc}, 质量: {quality})\n")
    print(f"{'文件名':<40} {'压缩前':>10} {'压缩后':>10} {'节省':>8}")
    print("-" * 72)

    # 创建输出目录
    output_dir = Path(folder) / "compressed"
    output_dir.mkdir(exist_ok=True)

    total_original = 0
    total_compressed = 0
    success_count = 0

    for img_path in images:
        try:
            original_size, compressed_size = compress_image(
                img_path, output_dir, scale, quality, fixed_width, fixed_height
            )
            saved = original_size - compressed_size
            percent = (saved / original_size * 100) if original_size > 0 else 0
            total_original += original_size
            total_compressed += compressed_size
            success_count += 1

            print(
                f"{img_path.name:<40} "
                f"{format_size(original_size):>10} "
                f"{format_size(compressed_size):>10} "
                f"{percent:>6.1f}%"
            )
        except Exception as e:
            print(f"{img_path.name:<40} 压缩失败: {e}")

    # 汇总统计
    total_saved = total_original - total_compressed
    total_percent = (total_saved / total_original * 100) if total_original > 0 else 0

    print("-" * 72)
    print(f"\n压缩完成！")
    print(f"  压缩图片数: {success_count} 张")
    print(f"  原始总大小: {format_size(total_original)}")
    print(f"  压缩后大小: {format_size(total_compressed)}")
    print(f"  节省空间:   {format_size(total_saved)} ({total_percent:.1f}%)")
    print(f"\n输出目录: {output_dir}")


if __name__ == "__main__":
    main()
