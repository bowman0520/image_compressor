# 本地图片压缩工具

一个简单实用的本地图片压缩程序，支持 JPG、JPEG、PNG、WEBP 格式。

## 功能特性

- 支持 JPG / JPEG / PNG / WEBP 图片格式
- 保持原始宽高比例，不改变图片尺寸
- JPG 和 WEBP 可自定义压缩质量（默认 75）
- PNG 自动转为 palette 模式或使用最高压缩级别，尽量压缩体积
- 压缩图片输出到原文件夹下的 `compressed` 子目录，不覆盖原图
- 压缩后文件名前缀加 `compressed_`
- 终端显示每张图片压缩前后大小及压缩百分比
- 最后输出汇总统计：压缩数量、节省空间

## 安装

```bash
# 建议使用虚拟环境
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# Linux / macOS 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

```bash
python compressor.py
```

运行后按提示操作：

1. 输入图片所在的文件夹路径
2. 输入 JPG/WEBP 的压缩质量（1-100，直接回车使用默认值 75）
3. 程序自动扫描、压缩并输出结果

### 示例

```
============================================================
  本地图片压缩工具
  支持: JPG / JPEG / PNG / WEBP
============================================================

请输入图片文件夹路径: D:\photos
请输入 JPG/WEBP 压缩质量 (1-100, 回车使用默认 75): 80

找到 3 张图片，开始压缩...

文件名                                     压缩前       压缩后     节省
------------------------------------------------------------------------
photo1.jpg                                2.3 MB      1.1 MB   52.2%
icon.png                                 45.2 KB     12.8 KB   71.7%
banner.webp                              890.5 KB    620.3 KB   30.4%
------------------------------------------------------------------------

压缩完成！
  压缩图片数: 3 张
  原始总大小: 3.22 MB
  压缩后大小: 1.73 MB
  节省空间:   1.49 MB (46.3%)

输出目录: D:\photos\compressed
```

## 输出说明

- 压缩后的图片保存在原文件夹下的 `compressed` 目录中
- 文件名格式：`compressed_原文件名.扩展名`
- 原始图片不会被修改或删除

## 压缩策略

| 格式 | 策略 |
|------|------|
| JPG/JPEG | 使用指定 quality 值压缩 + optimize 优化 |
| WEBP | 使用指定 quality 值 + method=6 (最高压缩) |
| PNG (无透明) | 转 palette 模式 + compress_level=9 |
| PNG (有透明) | 保留 RGBA + optimize + compress_level=9 |
