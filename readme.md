# 使用说明

## 脚本功能简介
本工具用于将 Excel 翻译文件 (`.xlsx`) 自动同步到 Android 项目的 `strings.xml` 资源文件中，支持多语言自动分发。

## 调用方式

```bash
python xlsx_to_android_strings.py "翻译文件xlsx路径" "目标项目res路径"
```

> **注意**：目标 `res` 路径下必须包含相应的多语言资源文件夹（例如：`values`, `values-zh-rCN` 等）。

## 功能特性

* **智能映射**：读取 Excel 第一行作为表头，自动识别 `key` 列及各语言列。
* **自动归档**：根据语言标识（如 `values-zh-rCN`）自动定位至对应的资源文件夹。
* **文件处理**：
    * 自动创建不存在的文件夹和 `strings.xml` 文件。
    * 将翻译内容写入目标 `strings.xml`。
* **数据清洗与优化**：
    * 如果翻译内容为空，则跳过不写入。
    * 如果整行为空，自动跳过。
    * **更新机制**：已存在的 `key` 会自动更新翻译内容，新 `key` 会追加到文件末尾。

## 翻译文件格式参考

建议参考以下结构准备您的 `翻译.xlsx`：

| key | values | values-zh-rCN | ... |
| :--- | :--- | :--- | :--- |
| app_name | Video Downloader | 视频下载器 | ... |
| download_success | Download complete | 下载完成 | ... |

---
