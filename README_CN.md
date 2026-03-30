<div align="center">

# SoPDF

**属于所有人的 PDF 处理库。**

[![PyPI version](https://img.shields.io/pypi/v/sopdf.svg)](https://pypi.org/project/sopdf/)
[![Python versions](https://img.shields.io/pypi/pyversions/sopdf.svg)](https://pypi.org/project/sopdf/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

```
pip install sopdf
```

</div>

---

## 为什么选择 SoPDF？

对于开发者来说，一个功能全面的开源 PDF 处理库，通常伴随着对开源生态不友好的License。如果你以宽松许可证发布产品，或者参与一个会被他人自由嵌入的库，License 就会成为真实的障碍。但高性能和功能全面性又是 PDF 处理不可或缺的开发需求。

**SoPDF 就是为填补这一空白而生的。**

基于 [`pypdfium2`](https://github.com/pypdfium2-team/pypdfium2)（Google PDFium，负责渲染与文本）和 [`pikepdf`](https://github.com/pikepdf/pikepdf)（libqpdf，负责结构与写入），SoPDF 在 **Apache 2.0 许可证** 下提供同等核心能力——无附加条件，无需许可证审计，零摩擦。嵌入它、发布它、fork 它，它是你的。

除许可证优势之外，SoPDF 在性能上也**全面领先**于主流竞品：渲染速度最高快 **1.56 倍**，纯文本提取快 **2.7 倍**，全文搜索快 **3 倍**——且与 PyMuPDF 保持 99% 的词级准确率一致性。详见 [性能基准](#性能基准) 章节，或亲自运行验证。

---

## 功能特性

| 能力 | SoPDF API |
|---|---|
| 从路径 / 字节 / 流打开 | `sopdf.open()` |
| 将页面渲染为 PNG / JPEG | `page.render(dpi=300)` |
| 批量与并行渲染 | `sopdf.render_pages(pages, parallel=True)` |
| 提取纯文本 | `page.get_text()` |
| 提取带边界框的文本 | `page.get_text_blocks()` |
| 全文搜索并返回命中矩形 | `page.search("keyword")` |
| 将页面拆分为新文档 | `doc.split(pages=[0, 1, 2])` |
| 合并多个 PDF | `sopdf.merge(["a.pdf", "b.pdf"], output="merged.pdf")` |
| 压缩保存 | `doc.save("out.pdf", compress=True, garbage=True)` |
| 序列化为字节（不写磁盘） | `doc.to_bytes()` |
| 旋转页面 | `page.rotation = 90` |
| 打开并保存加密 PDF | `sopdf.open("enc.pdf", password="secret")` |
| 自动修复损坏的 PDF | `sopdf.open("corrupted.pdf")` |

---

## 快速上手

```python
import sopdf

# 打开——得益于懒加载与 mmap，几乎瞬间完成
with sopdf.open("document.pdf") as doc:
    print(f"{doc.page_count} 页  •  {doc.metadata['title']}")

    # 以 150 DPI 渲染第 0 页
    img_bytes = doc[0].render(dpi=150)           # PNG 字节
    doc[0].render_to_file("page0.png", dpi=300)  # 写入磁盘

    # 提取文本
    text = doc[0].get_text()
    blocks = doc[0].get_text_blocks()            # list[TextBlock]

    # 搜索
    hits = doc[0].search("invoice", match_case=False)
    for rect in hits:
        print(f"  匹配位置 {rect}")
```

### 拆分与合并

```python
# 提取前 3 页
new_doc = doc.split(pages=[0, 1, 2], output="chapter1.pdf")

# 将每一页拆分为独立文件
doc.split_each(output_dir="pages/")

# 合并文件列表
sopdf.merge(["intro.pdf", "body.pdf", "appendix.pdf"], output="book.pdf")

# 或以编程方式追加
doc_a.append(doc_b)
doc_a.save("combined.pdf")
```

### 并行渲染整份文档

```python
with sopdf.open("report.pdf") as doc:
    images = sopdf.render_pages(
        doc.pages,
        dpi=150,
        format="png",
        parallel=True,   # 多进程——绕过 GIL
    )
```

### 解密并去除密码保存

```python
with sopdf.open("protected.pdf", password="hunter2") as doc:
    doc.save("unlocked.pdf")  # 保存时自动去除加密
```

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

## 安装

```bash
pip install sopdf
```

要求 Python 3.10+。两个原生依赖（`pypdfium2`、`pikepdf`）均为 macOS、Linux 和 Windows 提供预编译 wheel——无需编译器。

---

## API 参考

### `sopdf.open(path=None, password=None, *, stream=None) → Document`

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | `str \| Path` | PDF 文件路径 |
| `password` | `str` | 加密 PDF 的密码 |
| `stream` | `bytes` | 从原始字节打开，而非文件 |

### `Document`

| 成员 | 类型 | 说明 |
|---|---|---|
| `page_count` | `int` | 总页数 |
| `metadata` | `dict` | 标题、作者、主题、创建者、生产者、日期 |
| `is_encrypted` | `bool` | 文档是否设有密码保护 |
| `doc[i]` / `doc.load_page(i)` | `Page` | 通过 0-based 索引访问页面 |
| `doc.pages` | sequence | 所有页面的可迭代对象 |
| `doc.split(pages, output=None)` | `Document` | 提取页面子集 |
| `doc.split_each(output_dir)` | — | 将每页保存为独立文件 |
| `doc.append(other)` | — | 追加另一份文档的页面 |
| `doc.save(path, *, compress, garbage, linearize)` | — | 保存到磁盘 |
| `doc.to_bytes(*, compress)` | `bytes` | 序列化为字节 |
| `doc.close()` | — | 释放文件句柄 |

### `Page`

| 成员 | 类型 | 说明 |
|---|---|---|
| `number` | `int` | 0-based 页面索引 |
| `rect` | `Rect` | 以点为单位的页面尺寸 |
| `rotation` | `int` | 页面旋转角度（0 / 90 / 180 / 270） |
| `render(dpi, format, alpha)` | `bytes` | 渲染为 PNG / JPEG |
| `render_to_file(path, dpi, format, alpha)` | — | 渲染并保存 |
| `get_text(rect=None)` | `str` | 提取纯文本 |
| `get_text_blocks(rect=None, format="list")` | `list` | 结构化文本块 |
| `search(query, match_case=False)` | `list[Rect]` | 搜索文本，返回命中矩形 |
| `search_text_blocks(query, match_case=False)` | `list[dict]` | 搜索文本并附带上下文 |

### 异常

```python
sopdf.PDFError        # 基类——RuntimeError 的子类
sopdf.PasswordError   # 密码错误或缺失
sopdf.FileDataError   # PDF 损坏或无法读取
sopdf.PageError       # 页面索引无效或旋转角度非法
```

---

## 许可证

Apache 2.0——详见 [LICENSE](LICENSE)。

SoPDF 可自由用于个人项目、商业产品和开源库。无需许可费，除标准 Apache 2.0 声明外无需任何署名要求。
