# SoPDF API 参考

## 目录

- [顶层函数](#顶层函数)
  - [open()](#sopdfopenpath-password-stream)
  - [merge()](#sopdfmergeinputs-output)
  - [render\_pages()](#sopdfrender_pagespages-dpi-format-alpha-parallel)
  - [render\_pages\_to\_files()](#sopdfrender_pages_to_filespages-output_dir-dpi-format-alpha-parallel)
- [Document](#document)
  - [属性](#document-属性)
  - [页面访问](#页面访问)
  - [分割](#分割)
  - [合并](#合并)
  - [保存](#保存)
  - [生命周期](#生命周期)
- [Page](#page)
  - [属性](#page-属性)
  - [渲染](#渲染)
  - [文本提取](#文本提取)
  - [文本搜索](#文本搜索)
- [数据类型](#数据类型)
  - [Rect](#rect)
  - [TextBlock](#textblock)
- [异常](#异常)

---

## 顶层函数

### `sopdf.open(path, password, *, stream)`

打开一个 PDF 文档，返回 `Document` 实例。

```python
sopdf.open(
    path: str | pathlib.Path | None = None,
    password: str | None = None,
    *,
    stream: bytes | None = None,
) -> Document
```

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `path` | `str \| Path \| None` | `None` | PDF 文件的路径。与 `stream` 二选一。 |
| `password` | `str \| None` | `None` | 加密 PDF 的密码。无密码或密码不需要时传 `None`。 |
| `stream` | `bytes \| None` | `None` | 直接从内存字节打开，与 `path` 二选一。 |

**返回值**

`Document` — 打开的文档对象。

**异常**

| 异常 | 触发条件 |
|---|---|
| `PasswordError` | 文档需要密码，但未提供或密码错误。 |
| `FileDataError` | 文件损坏或无法解析为有效 PDF。 |

**示例**

```python
# 从文件路径打开
doc = sopdf.open("report.pdf")

# 打开加密文档
doc = sopdf.open("secure.pdf", password="hunter2")

# 从内存字节打开
with open("report.pdf", "rb") as f:
    doc = sopdf.open(stream=f.read())

# 推荐使用上下文管理器，自动释放资源
with sopdf.open("report.pdf") as doc:
    print(doc.page_count)
```

---

### `sopdf.merge(inputs, output)`

将多个 PDF 文件按顺序合并为一个输出文件。

```python
sopdf.merge(
    inputs: list[str | pathlib.Path],
    output: str | pathlib.Path,
) -> None
```

**参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `inputs` | `list[str \| Path]` | 待合并的 PDF 文件路径列表，按列表顺序拼接。 |
| `output` | `str \| Path` | 输出文件的目标路径。 |

**异常**

| 异常 | 触发条件 |
|---|---|
| `ValueError` | `inputs` 列表为空。 |
| `PasswordError` | 某个输入文件需要密码。 |
| `FileDataError` | 某个输入文件无法读取。 |

**示例**

```python
sopdf.merge(
    ["intro.pdf", "body.pdf", "appendix.pdf"],
    output="book.pdf",
)
```

---

### `sopdf.render_pages(pages, *, dpi, format, alpha, parallel)`

批量将一组页面渲染为图像字节。

```python
sopdf.render_pages(
    pages: list[Page],
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> list[bytes]
```

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `pages` | `list[Page]` | — | 待渲染的页面对象列表，通常来自 `doc.pages`。 |
| `dpi` | `int` | `72` | 渲染分辨率（每英寸点数）。常用值：72（屏幕预览）、150（高清）、300（印刷）。 |
| `format` | `str` | `"png"` | 输出图像格式，`"png"` 或 `"jpeg"`。 |
| `alpha` | `bool` | `False` | 是否包含透明通道（仅 PNG 有效）。 |
| `parallel` | `bool` | `False` | 是否使用多进程并行渲染。开启后可绕过 GIL，多核机器上大幅提速。 |

**返回值**

`list[bytes]` — 与 `pages` 一一对应的编码图像字节列表。

**示例**

```python
with sopdf.open("report.pdf") as doc:
    # 顺序渲染
    images = sopdf.render_pages(doc.pages, dpi=150)

    # 多进程并行渲染（大文档推荐）
    images = sopdf.render_pages(doc.pages, dpi=300, parallel=True)
```

---

### `sopdf.render_pages_to_files(pages, output_dir, *, dpi, format, alpha, parallel)`

批量渲染页面并将结果写入目录，文件名为 `page_0.png`、`page_1.png` 等。

```python
sopdf.render_pages_to_files(
    pages: list[Page],
    output_dir: str | pathlib.Path,
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
    parallel: bool = False,
) -> None
```

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `pages` | `list[Page]` | — | 待渲染的页面对象列表。 |
| `output_dir` | `str \| Path` | — | 输出目录路径，不存在时自动创建。 |
| `dpi` | `int` | `72` | 渲染分辨率（每英寸点数）。 |
| `format` | `str` | `"png"` | 输出图像格式，`"png"` 或 `"jpeg"`。 |
| `alpha` | `bool` | `False` | 是否包含透明通道（仅 PNG 有效）。 |
| `parallel` | `bool` | `False` | 是否使用多进程并行渲染。 |

**示例**

```python
with sopdf.open("report.pdf") as doc:
    sopdf.render_pages_to_files(doc.pages, "output/", dpi=150, parallel=True)
# 生成 output/page_0.png, output/page_1.png, ...
```

---

## Document

`Document` 表示一个已打开的 PDF 文档。不应直接构造，始终通过 `sopdf.open()` 获取。

---

### Document 属性

#### `page_count`

```python
doc.page_count -> int
```

文档的总页数（只读）。

---

#### `metadata`

```python
doc.metadata -> dict
```

文档元数据字典（只读）。键名均为小写字符串，可能包含以下字段：

| 键 | 类型 | 说明 |
|---|---|---|
| `"title"` | `str` | 文档标题 |
| `"author"` | `str` | 作者 |
| `"subject"` | `str` | 主题 |
| `"creator"` | `str` | 创建应用程序 |
| `"producer"` | `str` | 生成 PDF 的工具 |
| `"creation_date"` | `str` | 创建日期 |
| `"mod_date"` | `str` | 最后修改日期 |

某些字段在特定文档中可能不存在。

---

#### `is_encrypted`

```python
doc.is_encrypted -> bool
```

文档是否设有密码保护（只读）。即使提供了正确密码并成功打开，该属性仍返回 `True`。

---

#### `pages`

```python
doc.pages -> _PageList
```

所有页面的惰性序列（只读）。支持迭代和切片，常与 `render_pages()` 配合使用。

---

### 页面访问

#### `doc[index]` / `doc.load_page(index)`

```python
doc[index: int] -> Page
doc.load_page(index: int) -> Page
```

通过 0-based 索引获取页面。支持负数索引（`doc[-1]` 为最后一页）。

**异常**

| 异常 | 触发条件 |
|---|---|
| `PageError` | 索引超出范围。 |

**示例**

```python
first_page = doc[0]
last_page  = doc[-1]
third_page = doc.load_page(2)
```

---

#### `len(doc)`

```python
len(doc) -> int
```

等同于 `doc.page_count`。

---

#### 迭代

```python
for page in doc:
    print(page.number)
```

---

### 分割

#### `doc.split(pages, output)`

```python
doc.split(
    pages: list[int],
    output: str | pathlib.Path | None = None,
) -> Document
```

从当前文档中提取指定页面，返回一个新的 `Document` 对象。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `pages` | `list[int]` | — | 待提取的页面 0-based 索引列表，顺序与列表顺序一致。 |
| `output` | `str \| Path \| None` | `None` | 若提供，则同时将新文档写入该路径；否则仅在内存中返回。 |

**返回值**

`Document` — 包含指定页面的新文档对象。

**示例**

```python
# 提取前 3 页并保存
chapter = doc.split(pages=[0, 1, 2], output="chapter1.pdf")

# 仅在内存中提取，不写磁盘
excerpt = doc.split(pages=[4, 5, 6])
```

---

#### `doc.split_each(output_dir)`

```python
doc.split_each(output_dir: str | pathlib.Path) -> None
```

将文档的每一页分别保存为独立的 PDF 文件，文件名格式为 `page_0.pdf`、`page_1.pdf` 等。

**参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `output_dir` | `str \| Path` | 输出目录路径，不存在时自动创建。 |

**示例**

```python
doc.split_each("pages/")
# 生成 pages/page_0.pdf, pages/page_1.pdf, ...
```

---

### 合并

#### `doc.append(other)`

```python
doc.append(other: Document) -> None
```

将另一个文档的所有页面追加到当前文档末尾。调用后文档被标记为"已修改"，需调用 `save()` 或 `to_bytes()` 持久化。

**参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `other` | `Document` | 被追加的文档对象。 |

**示例**

```python
with sopdf.open("part1.pdf") as doc_a, sopdf.open("part2.pdf") as doc_b:
    doc_a.append(doc_b)
    doc_a.save("combined.pdf")
```

---

### 保存

#### `doc.save(path, *, compress, garbage, linearize)`

```python
doc.save(
    path: str | pathlib.Path,
    *,
    compress: bool = True,
    garbage: bool = False,
    linearize: bool = False,
) -> None
```

将文档写入磁盘。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `path` | `str \| Path` | — | 目标文件路径。 |
| `compress` | `bool` | `True` | 是否压缩内容流，可显著减小文件体积。 |
| `garbage` | `bool` | `False` | 是否生成对象流（object streams），进一步压缩结构数据。 |
| `linearize` | `bool` | `False` | 是否线性化 PDF，优化网络顺序读取（Fast Web View）。 |

**示例**

```python
# 普通保存（压缩开启）
doc.save("output.pdf")

# 最大压缩
doc.save("output.pdf", compress=True, garbage=True)

# 去除加密（以正确密码打开后保存）
doc.save("unlocked.pdf")
```

---

#### `doc.to_bytes(*, compress)`

```python
doc.to_bytes(compress: bool = True) -> bytes
```

将文档序列化为字节，不写入磁盘。适用于在内存中处理或通过网络传输 PDF。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `compress` | `bool` | `True` | 是否压缩内容流。 |

**返回值**

`bytes` — 完整的 PDF 文件字节内容。

**示例**

```python
pdf_bytes = doc.to_bytes()

# 在 Flask 中作为响应直接返回
from flask import Response
return Response(doc.to_bytes(), mimetype="application/pdf")
```

---

### 生命周期

#### `doc.close()`

```python
doc.close() -> None
```

关闭文档，释放所有文件句柄和内存资源。推荐使用 `with` 语句自动管理，避免手动调用。

---

#### 上下文管理器

```python
with sopdf.open("file.pdf") as doc:
    ...
# 退出 with 块时自动调用 close()
```

---

## Page

`Page` 表示文档中的单个页面。通过 `doc[i]` 或 `doc.load_page(i)` 获取，不应直接构造。

---

### Page 属性

#### `number`

```python
page.number -> int
```

页面的 0-based 索引（只读）。

---

#### `rect`

```python
page.rect -> Rect
```

页面尺寸，单位为 PDF 点（1 pt = 1/72 英寸）（只读）。`rect.width` 和 `rect.height` 为页面的宽高。

---

#### `rotation`

```python
page.rotation -> int          # 读取当前旋转角度
page.rotation = degrees: int  # 设置旋转角度
```

页面旋转角度，取值为 `0`、`90`、`180`、`270` 之一（可读写）。

**异常**

| 异常 | 触发条件 |
|---|---|
| `PageError` | 设置了非 0/90/180/270 的值。 |

---

### 渲染

#### `page.render(*, dpi, format, alpha)`

```python
page.render(
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
) -> bytes
```

将页面渲染为图像字节。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `dpi` | `int` | `72` | 渲染分辨率（每英寸点数）。72 适合屏幕预览，300 适合印刷质量。 |
| `format` | `str` | `"png"` | 输出格式，`"png"` 或 `"jpeg"`。 |
| `alpha` | `bool` | `False` | 是否包含透明通道（Alpha）。仅 PNG 格式有效；JPEG 不支持透明度。 |

**返回值**

`bytes` — 编码后的图像字节（PNG 或 JPEG）。

**示例**

```python
png_bytes  = page.render(dpi=150)
jpeg_bytes = page.render(dpi=150, format="jpeg")
png_alpha  = page.render(dpi=72, alpha=True)
```

---

#### `page.render_to_file(path, *, dpi, format, alpha)`

```python
page.render_to_file(
    path: str | pathlib.Path,
    *,
    dpi: int = 72,
    format: str = "png",
    alpha: bool = False,
) -> None
```

渲染页面并将图像写入文件。参数含义与 `render()` 完全一致。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `path` | `str \| Path` | — | 输出文件路径（含扩展名）。 |
| `dpi` | `int` | `72` | 渲染分辨率（每英寸点数）。 |
| `format` | `str` | `"png"` | 输出格式，`"png"` 或 `"jpeg"`。 |
| `alpha` | `bool` | `False` | 是否包含透明通道（仅 PNG）。 |

**示例**

```python
page.render_to_file("page0.png", dpi=300)
page.render_to_file("page0.jpg", dpi=150, format="jpeg")
```

---

### 文本提取

#### `page.get_text(*, rect)`

```python
page.get_text(
    *,
    rect: Rect | None = None,
) -> str
```

提取页面的纯文本内容。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rect` | `Rect \| None` | `None` | 仅提取该矩形区域内的文本；为 `None` 时提取整页。 |

**返回值**

`str` — 提取到的纯文本字符串。

**示例**

```python
full_text = page.get_text()

# 仅提取特定区域
region = Rect(0, 0, 300, 100)
header_text = page.get_text(rect=region)
```

---

#### `page.get_text_blocks(*, rect, format)`

```python
page.get_text_blocks(
    *,
    rect: Rect | None = None,
    format: str = "list",
) -> list
```

提取带边界框的结构化文本块。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rect` | `Rect \| None` | `None` | 仅提取该矩形区域内的文本块；为 `None` 时提取整页。 |
| `format` | `str` | `"list"` | 返回格式。`"list"` 返回 `TextBlock` 对象列表；`"dict"` 返回字典列表，每个字典含 `"text"` 和 `"rect"` 键。 |

**返回值**

- `format="list"` 时：`list[TextBlock]`
- `format="dict"` 时：`list[dict]`，每个字典形如 `{"text": "...", "rect": {"x0": ..., "y0": ..., "x1": ..., "y1": ...}}`

**示例**

```python
blocks = page.get_text_blocks()
for block in blocks:
    print(block.text, block.rect)

# 以字典格式返回（便于 JSON 序列化）
dicts = page.get_text_blocks(format="dict")
```

---

### 文本搜索

#### `page.search(query, *, match_case)`

```python
page.search(
    query: str,
    *,
    match_case: bool = False,
) -> list[Rect]
```

在页面上搜索文本，返回所有命中位置的矩形区域列表。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `query` | `str` | — | 要搜索的文本字符串。 |
| `match_case` | `bool` | `False` | 是否区分大小写。默认不区分。 |

**返回值**

`list[Rect]` — 每个命中位置的边界矩形列表。未找到时返回空列表。

**示例**

```python
hits = page.search("invoice")
for rect in hits:
    print(f"在 {rect} 处找到匹配")

# 区分大小写
hits = page.search("PDF", match_case=True)
```

---

#### `page.search_text_blocks(query, *, match_case)`

```python
page.search_text_blocks(
    query: str,
    *,
    match_case: bool = False,
) -> list[dict]
```

搜索文本，同时返回每处命中的精确矩形及其所在的完整文本块上下文。

**参数**

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `query` | `str` | — | 要搜索的文本字符串。 |
| `match_case` | `bool` | `False` | 是否区分大小写。 |

**返回值**

`list[dict]` — 每个元素为一个字典，包含以下键：

| 键 | 类型 | 说明 |
|---|---|---|
| `"text"` | `str` | 命中所在文本块的完整文本内容。 |
| `"rect"` | `Rect` | 命中所在文本块的边界矩形。 |
| `"match_rect"` | `Rect` | 命中关键词本身的精确边界矩形。 |

**示例**

```python
results = page.search_text_blocks("total amount")
for r in results:
    print(r["text"])        # 包含关键词的完整段落
    print(r["match_rect"])  # 关键词精确位置
```

---

## 数据类型

### Rect

表示一个矩形区域，坐标单位为 PDF 点（pt）。坐标系以页面左上角为原点，x 向右增大，y 向下增大。

```python
Rect(x0: float, y0: float, x1: float, y1: float)
```

**构造参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `x0` | `float` | 左边界（左上角 x 坐标）。 |
| `y0` | `float` | 上边界（左上角 y 坐标）。 |
| `x1` | `float` | 右边界（右下角 x 坐标）。 |
| `y1` | `float` | 下边界（右下角 y 坐标）。 |

**属性**

| 属性 | 类型 | 说明 |
|---|---|---|
| `x0` | `float` | 左边界。 |
| `y0` | `float` | 上边界。 |
| `x1` | `float` | 右边界。 |
| `y1` | `float` | 下边界。 |
| `width` | `float` | 矩形宽度，等于 `x1 - x0`。 |
| `height` | `float` | 矩形高度，等于 `y1 - y0`。 |
| `is_valid` | `bool` | 当 `x0 ≤ x1` 且 `y0 ≤ y1` 时为 `True`。 |
| `is_empty` | `bool` | 矩形面积为零时为 `True`。 |

**方法**

| 方法 | 返回值 | 说明 |
|---|---|---|
| `get_area()` | `float` | 矩形面积；无效矩形返回 `0`。 |
| `contains(other)` | `bool` | `other` 为 `Rect` 时判断是否完全包含；`other` 为 `(x, y)` 元组时判断点是否在内。 |
| `intersects(other)` | `bool` | 判断两矩形是否重叠（边界接触也算）。 |
| `intersect(other)` | `Rect` | 返回两矩形的交集区域；不重叠时返回空矩形。 |
| `include_rect(other)` | `Rect` | 返回同时包含两个矩形的最小外接矩形。 |
| `include_point(x, y)` | `Rect` | 返回扩展到包含指定点的新矩形。 |

所有几何运算均返回新的 `Rect` 实例，原对象不可变。

**示例**

```python
r = Rect(10, 20, 200, 300)
print(r.width)    # 190.0
print(r.height)   # 280.0

# 判断包含
print(r.contains(Rect(50, 50, 100, 100)))  # True
print(r.contains((50, 50)))                # True（点）

# 交集
a = Rect(0, 0, 100, 100)
b = Rect(50, 50, 150, 150)
print(a.intersect(b))  # Rect(50, 50, 100, 100)

# 解包
x0, y0, x1, y1 = r
```

---

### TextBlock

表示页面上一个带边界框的文本块。

```python
TextBlock(text: str, rect: Rect)
```

**属性**

| 属性 | 类型 | 说明 |
|---|---|---|
| `text` | `str` | 文本块的文字内容。 |
| `rect` | `Rect` | 文本块在页面上的边界矩形。 |

**方法**

| 方法 | 返回值 | 说明 |
|---|---|---|
| `to_dict()` | `dict` | 转换为字典，含 `"text"` 和 `"rect"` 键；其中 `"rect"` 为含 `"x0"`、`"y0"`、`"x1"`、`"y1"` 的字典。 |

**示例**

```python
blocks = page.get_text_blocks()
for block in blocks:
    print(block.text)
    print(block.rect.width, block.rect.height)
    print(block.to_dict())
```

---

## 异常

所有异常均继承自 `PDFError`，后者继承自内置 `RuntimeError`。

```
RuntimeError
└── PDFError
    ├── PasswordError
    ├── FileDataError
    └── PageError
```

| 异常类 | 触发场景 |
|---|---|
| `PDFError` | 所有 sopdf 异常的基类，可用于统一捕获。 |
| `PasswordError` | 打开加密 PDF 时密码缺失或错误。 |
| `FileDataError` | PDF 文件损坏、格式非法或无法解析。 |
| `PageError` | 页面索引超出范围，或设置了非法旋转角度（非 0/90/180/270）。 |

**示例**

```python
import sopdf

try:
    doc = sopdf.open("file.pdf", password="wrong")
except sopdf.PasswordError:
    print("密码错误")
except sopdf.FileDataError:
    print("文件损坏")
except sopdf.PDFError as e:
    print(f"PDF 错误：{e}")
```
