#!/usr/bin/env python3
"""
将xlsx翻译文件写入Android项目的strings.xml翻译文件中

使用方法:
python xlsx_to_android_strings.py <xlsx文件路径> <安卓res路径>

xlsx文件格式:
- 第一行: 表头，第一列必须是"key"，后面各列是语言标识(如value-zh-rCN, values-ar等)
- 第二行开始: 第一列是翻译条目的key，后面各列是对应语言的翻译内容
"""

import sys
import os
import re
import xml.etree.ElementTree as ET
from openpyxl import load_workbook


def parse_header(header_row):
    """
    解析表头行，返回语言列的映射
    第一列必须是key，后面各列是语言标识
    """
    language_columns = {}
    
    for col_idx, cell in enumerate(header_row, start=1):
        if col_idx == 1:
            if cell and cell.lower() == 'key':
                continue
            else:
                raise ValueError(f"第一列必须是'key'，但实际是: {cell}")
        else:
            if cell:
                language_columns[col_idx] = cell.strip()
    
    return language_columns


def find_strings_xml(res_path, language_folder):
    """
    找到或创建对应语言的strings.xml文件
    """
    if not language_folder.startswith('values'):
        language_folder = 'values-' + language_folder
    
    folder_path = os.path.join(res_path, language_folder)
    strings_xml_path = os.path.join(folder_path, 'strings.xml')
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"创建文件夹: {folder_path}")
    
    if not os.path.exists(strings_xml_path):
        with open(strings_xml_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<resources>\n</resources>\n')
        print(f"创建新的strings.xml: {strings_xml_path}")
    
    return strings_xml_path


def escape_xml_text(text):
    """转义XML特殊字符"""
    if not text:
        return ''
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def get_existing_string_names(file_path):
    """Return existing string names without rewriting the XML."""
    tree = ET.parse(file_path)
    return {
        string_elem.get('name')
        for string_elem in tree.getroot().findall('string')
        if string_elem.get('name')
    }


def update_and_append_strings(file_path, replacements, additions):
    """Replace existing string text and append new strings without reformatting XML."""
    if not replacements and not additions:
        return

    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    for key, value in replacements:
        escaped_key = re.escape(key)
        pattern = re.compile(
            r'(<string\b(?=[^>]*\bname\s*=\s*["\']' + escaped_key +
            r'["\'])[^>]*>)(.*?)(</string>)',
            re.DOTALL,
        )
        content, count = pattern.subn(
            lambda match: match.group(1) + escape_xml_text(value) + match.group(3),
            content,
            count=1,
        )
        if count == 0:
            raise ValueError(f"无法替换 strings.xml 中的 key: {key}")

    if not additions:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        return

    closing_tag = '</resources>'
    closing_tag_index = content.rfind(closing_tag)
    if closing_tag_index == -1:
        raise ValueError(f"strings.xml 缺少 {closing_tag}: {file_path}")

    line_ending = '\r\n' if '\r\n' in content else '\n'
    prefix = content[:closing_tag_index]
    suffix = content[closing_tag_index:]
    if prefix and not prefix.endswith(('\n', '\r')):
        prefix += line_ending

    new_lines = [
        f'\t<string name="{key}">{escape_xml_text(value)}</string>'
        for key, value in additions.items()
    ]
    content = prefix + line_ending.join(new_lines) + line_ending + suffix

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def process_xlsx(xlsx_path, res_path):
    """
    处理xlsx文件并写入翻译
    """
    if not os.path.exists(xlsx_path):
        print(f"错误: xlsx文件不存在: {xlsx_path}")
        return
    
    if not os.path.exists(res_path):
        print(f"错误: res目录不存在: {res_path}")
        return
    
    wb = load_workbook(xlsx_path)
    ws = wb.active
    
    header_row = []
    for cell in ws[1]:
        header_row.append(cell.value)
    
    print(f"表头: {header_row}")
    
    language_columns = parse_header(header_row)
    print(f"找到语言列: {language_columns}")
    
    xml_files = {}
    
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
        key_cell = row[0]
        key = key_cell.value if key_cell else None
        
        if not key:
            all_empty = True
            for cell in row:
                if cell.value:
                    all_empty = False
                    break
            
            if all_empty:
                print(f"跳过空行: 第{row_idx}行")
                continue
            else:
                print(f"警告: 第{row_idx}行key为空，但有翻译内容，跳过")
                continue
        
        key = str(key).strip()
        
        for col_idx, language in language_columns.items():
            cell = row[col_idx - 1] if col_idx - 1 < len(row) else None
            value = cell.value if cell else None
            
            if not value or str(value).strip() == '':
                continue
            
            value = str(value).strip()
            
            if language not in xml_files:
                strings_xml_path = find_strings_xml(res_path, language)
                xml_files[language] = {
                    'path': strings_xml_path,
                    'original_names': get_existing_string_names(strings_xml_path),
                    'replacements': [],
                    'additions': {}
                }
            
            data = xml_files[language]
            if key in data['original_names']:
                data['replacements'].append((key, value))
                print(f"替换已有翻译: {language}/{key} = {value}")
                continue

            data['additions'][key] = value
            print(f"添加翻译: {language}/{key} = {value}")
    
    for language, data in xml_files.items():
        update_and_append_strings(data['path'], data['replacements'], data['additions'])
        print(f"已保存: {data['path']}")
    
    print("\n翻译写入完成!")


def main():
    if len(sys.argv) != 3:
        print("使用方法:")
        print("python xlsx_to_android_strings.py <xlsx文件路径> <安卓res路径>")
        print("\n示例:")
        print("python xlsx_to_android_strings.py translations.xlsx /path/to/android/app/src/main/res")
        sys.exit(1)
    
    xlsx_path = sys.argv[1]
    res_path = sys.argv[2]
    
    process_xlsx(xlsx_path, res_path)


if __name__ == '__main__':
    main()
