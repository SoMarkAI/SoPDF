<div align="center">

# SoPDF

**属于所有人的 PDF 处理库。**

[![PyPI version](https://img.shields.io/pypi/v/sopdf.svg)](https://pypi.org/project/sopdf/)
[![Python versions](https://img.shields.io/pypi/pyversions/sopdf.svg)](https://pypi.org/project/sopdf/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

```
pip install sopdf
```

[English](README.md) | 中文

</div>

---

## 为什么选择 SoPDF？

对于开发者来说，一个功能全面的开源 PDF 处理库，通常伴随着对开源生态不友好的License。如果你以宽松许可证发布产品，或者参与一个会被他人自由嵌入的库，License 就会成为真实的障碍。但高性能和功能全面性又是 PDF 处理不可或缺的开发需求。

**SoPDF 就是为填补这一空白而生的。**

基于 [`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2)（Google PDFium，负责渲染与文本）和 [`pikepdf`](https://github.com/pikepdf/pikepdf)（libqpdf，负责结构与写入），SoPDF 在 **Apache 2.0 许可证** 下提供同等核心能力——无附加条件，无需许可证审计，零摩擦。嵌入它、发布它、fork 它，它是你的。

除许可证优势之外，SoPDF 在性能上也**全面领先**于主流竞品：渲染速度最高快 **1.56 倍**，纯文本提取快 **2.7 倍**，全文搜索快 **3 倍**——且与 PyMuPDF 保持 99% 的词级准确率一致性。详见 [性能基准](#性能基准) 章节，或亲自运行验证。

---

## 性能基准

> 测试环境：Apple M 系列芯片（arm64，10 核），Python 3.10，50 页 PDF 测试文件。
> 在本地自行运行：`python tests/benchmark/run_benchmarks.py`

### 渲染性能 vs PyMuPDF

| 场景 | SoPDF | PyMuPDF | 速度提升 |
| --- | --- | --- | --- |
| 打开文档 | 0.1 ms | 0.2 ms | **快 1.39 倍** |
| 渲染 1 页 @ 72 DPI | 6.6 ms | 9.1 ms | **快 1.38 倍** |
| 渲染 1 页 @ 150 DPI | 20.0 ms | 30.3 ms | **快 1.51 倍** |
| 渲染 1 页 @ 300 DPI | 64.6 ms | 101.1 ms | **快 1.56 倍** |
| 50 页顺序渲染 @ 150 DPI | 966.9 ms | 1470.3 ms | **快 1.52 倍** |
| 50 页并行渲染 @ 150 DPI | 410.7 ms | 447.2 ms | **快 1.09 倍** |

SoPDF 在每个 DPI 档位均胜出，且分辨率越高优势越明显。在多进程并行模式下，SoPDF 相较自身顺序基准实现了 **2.35 倍的真实加速**。PyMuPDF 的多线程并行路径则适得其反——因 MuPDF 全局锁将并发渲染串行化，耗时反而退化至 1548.9 ms，比顺序执行还慢。

### 文本提取性能 vs PyMuPDF

| 场景 | SoPDF | PyMuPDF | 速度提升 |
| --- | --- | --- | --- |
| 纯文本提取 — 50 页 | 26.0 ms | 70.0 ms | **快 2.70 倍** |
| 文本块提取 — 50 页 | 63.6 ms | 70.4 ms | **快 1.11 倍** |
| 搜索关键词 — 50 页 | 30.2 ms | 91.0 ms | **快 3.01 倍** |
| 区域文本提取 — 50 页 | 27.6 ms | 39.6 ms | **快 1.43 倍** |

全文搜索是最亮眼的指标：**比 PyMuPDF 快 3 倍**；纯文本提取紧随其后，达 **2.7 倍**。准确性经过验证——sopdf 与 PyMuPDF 在同一文档上的词级重合率达 99%，速度优势并不以牺牲准确率为代价。

---

## 架构

SoPDF 并行运行两个业界顶尖的 C/C++ 引擎：

<table>
  <thead>
    <tr>
      <th colspan="2">SoPDF Python API</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>pypdfium2</strong><br><small>(Google PDFium)</small></td>
      <td><strong>pikepdf</strong><br><small>(libqpdf)</small></td>
    </tr>
    <tr>
      <td>
        <ul>
          <li>渲染</li>
          <li>文本提取</li>
          <li>搜索</li>
        </ul>
      </td>
      <td>
        <ul>
          <li>结构读取</li>
          <li>所有写入操作</li>
          <li>保存 / 压缩</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

**脏标记 + 热重载**机制保持两个引擎的同步：当你通过 pikepdf 进行写操作（如旋转页面）后，下一次读操作（如渲染）会自动将文档重新序列化到 pypdfium2——无需任何手动同步。

文件以**懒加载 / mmap** 方式打开——一个 500 MB 的 PDF 可在毫秒内打开，且只有你实际访问的页面才会被加载。

---

## 快速上手

```bash
pip install sopdf
```

要求 Python 3.10+。两个原生依赖（`pypdfium2`、`pikepdf`）均为 macOS、Linux 和 Windows 提供预编译 wheel——无需编译器。

```python
import sopdf

# --- 打开 ---
# 从文件路径打开（得益于懒加载与 mmap，几乎瞬间完成）
with sopdf.open("document.pdf") as doc:

    # --- 渲染 ---
    img_bytes = doc[0].render(dpi=150)            # PNG 字节
    doc[0].render_to_file("page0.png", dpi=300)   # 写入磁盘

    # 并行渲染所有页面
    images = sopdf.render_pages(doc.pages, dpi=150, parallel=True)

    # --- 提取文本 ---
    text = doc[0].get_text()
    blocks = doc[0].get_text_blocks()             # 带边界框的 list[TextBlock]

    # --- 搜索 ---
    hits = doc[0].search("invoice", match_case=False)   # list[Rect]

    # --- 拆分与合并 ---
    new_doc = doc.split(pages=[0, 1, 2], output="chapter1.pdf")
    doc.split_each(output_dir="pages/")
    sopdf.merge(["intro.pdf", "body.pdf"], output="book.pdf")

    # --- 保存 ---
    doc.append(new_doc)
    doc.save("out.pdf", compress=True, garbage=True)
    raw = doc.to_bytes()                          # 不写磁盘

    # --- 旋转 ---
    doc[0].rotation = 90

# --- 加密 PDF ---
with sopdf.open("protected.pdf", password="hunter2") as doc:
    doc.save("unlocked.pdf")                      # 保存时自动去除加密

# --- 从字节 / 流打开 ---
with open("document.pdf", "rb") as f:
    with sopdf.open(stream=f.read()) as doc:
        print(doc.page_count)

# --- 自动修复损坏的 PDF ---
with sopdf.open("corrupted.pdf") as doc:
    doc.save("repaired.pdf")
```

---

## 功能特性

| 能力 | 示例 |
|---|---|
| 从路径 / 字节 / 流打开 | [01_open](examples/01_open) |
| 将页面渲染为 PNG / JPEG | [02_render](examples/02_render) |
| 批量与并行渲染 | [02_render](examples/02_render) |
| 提取纯文本 | [03_extract_text](examples/03_extract_text) |
| 提取带边界框的文本 | [03_extract_text](examples/03_extract_text) |
| 全文搜索并返回命中矩形 | [04_search_text](examples/04_search_text) |
| 将页面拆分为新文档 | [05_split](examples/05_split) |
| 合并多个 PDF | [06_merge](examples/06_merge) |
| 压缩保存 | [07_save_compress](examples/07_save_compress) |
| 序列化为字节（不写磁盘） | [07_save_compress](examples/07_save_compress) |
| 旋转页面 | [08_rotate](examples/08_rotate) |
| 打开并保存加密 PDF | [09_decrypt](examples/09_decrypt) |
| 自动修复损坏的 PDF | [10_repair](examples/10_repair) |

---

## 许可证

Apache 2.0——详见 [LICENSE](LICENSE)。

SoPDF 可自由用于个人项目、商业产品和开源库。无需许可费，除标准 Apache 2.0 声明外无需任何署名要求。

## 微信交流群
<img src="./docs/assets/wechat.png" width="100">
