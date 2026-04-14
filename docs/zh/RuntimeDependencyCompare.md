# 运行时依赖选型：OpenCV vs Pillow

## 为什么 SoPDF 选择 OpenCV 而非 Pillow

SoPDF 使用 [`opencv-python`](https://pypi.org/project/opencv-python/) 作为图像编码的运行时依赖，而非更常见的 Pillow（PIL）。本文档解释了这一选择背后的逻辑，并附上支撑结论的 benchmark 数据。

---

## 背景

SoPDF 的 PDF 页面渲染流程如下：

1. **pypdfium2**（Google PDFium）将 PDF 页面光栅化为原始位图缓冲区。
2. 位图缓冲区转换为 Python 可访问的数组。
3. 数组编码为 PNG 或 JPEG 字节供输出使用。

其中第 1 步和第 3 步涉及图像库的调用。核心问题是：从 pypdfium2 位图到编码图像字节，什么路径最快？

---

## Pillow 方案（旧）

旧实现通过 pypdfium2 的 `bitmap.to_pil()` 辅助函数调用 Pillow：

```python
bitmap = pdfium_page.render(scale=scale)   # pypdfium2 渲染为 BGRx 位图
pil_image = bitmap.to_pil()               # 分配新的 PIL Image（RGBA 完整拷贝）
pil_image = pil_image.convert("RGB")      # 再次拷贝：RGBA → RGB
buf = io.BytesIO()
pil_image.save(buf, format="PNG")         # 编码写入 BytesIO
return buf.getvalue()
```

该路径的问题：
- `to_pil()` 分配一个全新的 PIL `Image` 对象——完整的内存拷贝。
- `.convert("RGB")` 为色彩空间转换再次分配一次拷贝。
- `save()` 写入 `BytesIO` 缓冲区，在最终提取字节前产生第三次分配。

---

## OpenCV 方案（当前）

当前实现使用 pypdfium2 官方的 NumPy 桥接接口（`bitmap.to_numpy()`）和 OpenCV 的 `cv2.imencode()`：

```python
# 直接渲染为 3 通道 BGR——无 padding 字节，无额外通道
bitmap = pdfium_page.render(
    scale=scale,
    force_bitmap_format=pdfium.raw.FPDFBitmap_BGR,
)
arr = bitmap.to_numpy()              # 零拷贝 NumPy 视图，共享位图缓冲区内存
_, encoded = cv2.imencode('.png', arr)
return bytes(encoded)
```

带 alpha 通道的 PNG：
```python
bitmap = pdfium_page.render(scale=scale, maybe_alpha=True)  # BGRA
arr = bitmap.to_numpy()                                      # 零拷贝视图
_, encoded = cv2.imencode('.png', arr)
return bytes(encoded)
```

优势：
- **`force_bitmap_format=FPDFBitmap_BGR`**：直接将页面渲染为 3 通道 BGR——OpenCV 的原生格式——彻底消除通道重排或 padding 裁剪。
- **`bitmap.to_numpy()`** 零拷贝：返回的 NumPy 数组与 pypdfium2 内部位图缓冲区共享内存，不复制任何像素数据。
- **`cv2.imencode()`** 是高度优化的 C++ 例程，直接从 NumPy 数组编码 PNG/JPEG，无中间 Python 对象，无额外分配。

这也是 pypdfium2 项目本身推荐的 OpenCV 对接方式。

---

## Benchmark 结果

测试环境：Apple M 系列芯片（arm64，10 核），Python 3.12，50 页 PDF 测试文件。

### 单页渲染

| 场景 | Pillow | OpenCV | 速度提升 |
|---|---|---|---|
| 渲染 1 页 @ 72 DPI  | 6.6 ms  | 4.1 ms  | **快 1.61 倍** |
| 渲染 1 页 @ 150 DPI | 20.0 ms | 11.7 ms | **快 1.71 倍** |
| 渲染 1 页 @ 300 DPI | 64.6 ms | 34.2 ms | **快 1.89 倍** |

### 全文档渲染（50 页 @ 150 DPI）

| 场景 | Pillow | OpenCV | 速度提升 |
|---|---|---|---|
| 顺序渲染 | 966.9 ms | 543 ms | **快 1.78 倍** |
| 并行渲染 | 410.7 ms | 418 ms | ≈ 持平 |

分辨率越高，提升越明显——因为更大的像素缓冲区会放大 Pillow 路径中内存分配与拷贝的开销。

并行场景基本持平，因为此时瓶颈在于进程启动开销和进程间通信，而非图像编码本身。

---

## 总结

| 评估维度 | Pillow | OpenCV |
|---|---|---|
| 数组转换 | 分配新 Image（完整拷贝） | 零拷贝 NumPy 视图 |
| 通道处理 | Python 层 `.convert()` 调用 | 通过 `force_bitmap_format` 消除 |
| 编码 | `save()` + `BytesIO` + `getvalue()` | `cv2.imencode()` 直接输出 |
| pypdfium2 官方支持 | ✅（`to_pil()`） | ✅（`to_numpy()`） |
| 相对 Pillow 的渲染速度提升 | — | **快 1.6 × – 1.9 ×** |

OpenCV 在后渲染流水线的每个环节都消除了多余的内存拷贝。对于一个以渲染性能为核心价值的库来说，它是正确的选择。
