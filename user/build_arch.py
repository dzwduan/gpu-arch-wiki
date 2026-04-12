#!/usr/bin/env python3
"""
build_arch.py — 从 NV微架构梳理.md 生成 HTML，替换 web/index.html 中的 NV 微架构 section。
用法：python3 user/build_arch.py
"""

import re
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
MD_FILE = SCRIPT_DIR / 'NV微架构梳理.md'
HTML_FILE = ROOT / 'web' / 'index.html'
SRC_IMAGES = SCRIPT_DIR / 'images'
DST_IMAGES = ROOT / 'web' / 'images'

# ── Markdown 解析 ──────────────────────────────────────────

def parse_md(text):
    """解析整个 md 文件，返回 (architectures, compare_table_md, compare_title)"""
    # 提取对比表标题
    title_match = re.search(r'^## (.+)', text, flags=re.MULTILINE)
    compare_title = title_match.group(1).strip() if title_match else '微架构演进对比'
    # 分离对比表
    compare_split = re.split(r'^## .+\s*$', text, maxsplit=1, flags=re.MULTILINE)
    if len(compare_split) > 1:
        # 表格在前面：compare_split[0] 为空或空白，[1] 包含表格 + 架构内容
        # 表格在后面：compare_split[0] 包含架构内容，[1] 包含表格
        before = compare_split[0].strip()
        after = compare_split[1].strip()
        if not before:
            # 表格在最前面，架构内容在后面
            # 从 after 中分离表格和架构块（第一个 --- 开头的 frontmatter）
            fm_match = re.search(r'\n---\n\n---\nid:', after)
            if fm_match:
                compare_md = after[:fm_match.start()].strip()
                arch_text = after[fm_match.start():].strip()
            else:
                compare_md = after
                arch_text = ''
        else:
            # 表格在末尾（原有逻辑）
            arch_text = before
            compare_md = after
    else:
        arch_text = text
        compare_md = ''

    # 找到所有 frontmatter 块：每个以 ---\nid: ... 开头
    # 用正则找到每个 --- 开头的 frontmatter 位置
    arch_blocks = re.split(r'\n---\n\n---\n', arch_text)
    # 第一个块以文件开头的 --- 开始
    architectures = []
    for block in arch_blocks:
        block = block.strip()
        if not block:
            continue
        # 确保块以 --- 开头（第一个块自带，后面的被 split 去掉了）
        if not block.startswith('---'):
            block = '---\n' + block
        arch = parse_arch_block(block)
        if arch:
            architectures.append(arch)

    return architectures, compare_md, compare_title


def parse_arch_block(block):
    """解析单个架构块：frontmatter + sections"""
    # 去掉末尾可能残留的 ---
    block = block.rstrip()
    if block.endswith('\n---'):
        block = block[:-4]

    # 提取 frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', block, re.DOTALL)
    if not fm_match:
        return None

    meta_text = fm_match.group(1)
    content = fm_match.group(2)

    meta = {}
    for line in meta_text.strip().split('\n'):
        m = re.match(r'^(\w[\w_]*)\s*:\s*(.+)$', line)
        if m:
            meta[m.group(1)] = m.group(2).strip()

    if 'id' not in meta:
        return None

    # 按 ### 分段
    sections = []
    parts = re.split(r'^### (.+)$', content, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ''
        sections.append({'title': title, 'body': body.strip()})

    return {**meta, 'sections': sections}


# ── Markdown → HTML 转换 ────────────────────────────────────

def inline_md(text):
    """行内 markdown：**粗体**, `code`, [链接](url), 裸 URL"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    text = re.sub(r'(?<!["\'>])(https?://[^\s<,，。）\)]+)', r'<a href="\1" target="_blank">\1</a>', text)
    return text


def parse_sm_config(body):
    """解析 SM 配置段为列表 [{label, value, highlight}]"""
    items = []
    for line in body.split('\n'):
        m = re.match(r'^-\s+(.+?):\s*(.+)$', line)
        if m:
            highlight = '[highlight]' in m.group(2)
            value = m.group(2).replace('[highlight]', '').strip()
            items.append({'label': m.group(1).strip(), 'value': value, 'highlight': highlight})
    return items


def notes_to_html(body):
    """将说明段的 markdown 转为 HTML"""
    lines = body.split('\n')
    html_parts = []
    in_list = False
    notes_to_html._in_sublist = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # 双图: [images: a.png | b.png]
        img2 = re.match(r'^\[images:\s*(.+?)\s*\|\s*(.+?)\s*\]$', line)
        if img2:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            cap_left, cap_right = '', ''
            if i + 1 < len(lines):
                cap_m = re.match(r'^\[captions:\s*(.+?)\s*\|\s*(.+?)\s*\]$', lines[i + 1])
                if cap_m:
                    cap_left, cap_right = cap_m.group(1).strip(), cap_m.group(2).strip()
                    i += 1
            html_parts.append(
                f'<div class="arch-content-row">'
                f'<div class="arch-figure-half">'
                f'<img src="images/{img2.group(1).strip()}" alt="{cap_left}">'
                f'{f"<div class=\"paper-figure-caption\">{cap_left}</div>" if cap_left else ""}'
                f'</div>'
                f'<div class="arch-figure-half">'
                f'<img src="images/{img2.group(2).strip()}" alt="{cap_right}">'
                f'{f"<div class=\"paper-figure-caption\">{cap_right}</div>" if cap_right else ""}'
                f'</div></div>'
            )
            i += 1
            continue

        # 单图: [image: a.png]
        img1 = re.match(r'^\[image:\s*(.+?)\s*\]$', line)
        if img1:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            caption = ''
            if i + 1 < len(lines):
                cap_m = re.match(r'^\[caption:\s*(.+?)\s*\]$', lines[i + 1])
                if cap_m:
                    caption = cap_m.group(1).strip()
                    i += 1
            html_parts.append(
                f'<div class="paper-figure" style="margin-top:12px">'
                f'<img src="images/{img1.group(1).strip()}" alt="{caption}" style="max-width:700px">'
                f'{f"<div class=\"paper-figure-caption\">{caption}</div>" if caption else ""}'
                f'</div>'
            )
            i += 1
            continue

        # 跳过独立的 caption 行（已被上面消费）
        if re.match(r'^\[captions?:', line):
            i += 1
            continue

        # 列表项（无序 - 或有序 1.），支持一级和二级（2+空格缩进）
        ul_m = re.match(r'^-\s+(.+)$', line)
        ol_m = re.match(r'^\d+\.\s+(.+)$', line)
        sub_ul_m = re.match(r'^ {2,}-\s+(.+)$', line)
        sub_ol_m = re.match(r'^ {2,}\d+\.\s+(.+)$', line)

        if sub_ul_m or sub_ol_m:
            # 二级列表项
            content = (sub_ul_m or sub_ol_m).group(1)
            tag = 'ul' if sub_ul_m else 'ol'
            if not getattr(notes_to_html, '_in_sublist', False):
                html_parts.append(f'<{tag} class="arch-sublist">')
                notes_to_html._in_sublist = tag
            elif notes_to_html._in_sublist != tag:
                html_parts.append(f'</{notes_to_html._in_sublist}>')
                html_parts.append(f'<{tag} class="arch-sublist">')
                notes_to_html._in_sublist = tag
            html_parts.append(f'<li>{inline_md(content)}</li>')
            i += 1
            continue
        else:
            if getattr(notes_to_html, '_in_sublist', False):
                html_parts.append(f'</{notes_to_html._in_sublist}>')
                notes_to_html._in_sublist = False

        if ul_m or ol_m:
            content = (ul_m or ol_m).group(1)
            new_type = 'ul' if ul_m else 'ol'
            if in_list and in_list != new_type:
                html_parts.append(f'</{in_list}>')
                in_list = False
            if not in_list:
                cls = ' class="arch-list"' if new_type == 'ul' else ' class="arch-list-ol"'
                html_parts.append(f'<{new_type}{cls}>')
                in_list = new_type
            html_parts.append(f'<li>{inline_md(content)}</li>')
            i += 1
            continue

        # 空行
        if line.strip() == '':
            if getattr(notes_to_html, '_in_sublist', False):
                html_parts.append(f'</{notes_to_html._in_sublist}>')
                notes_to_html._in_sublist = False
            if in_list:
                html_parts.append(f'</{in_list}>')
                in_list = False
            i += 1
            continue

        # 普通段落
        if getattr(notes_to_html, '_in_sublist', False):
            html_parts.append(f'</{notes_to_html._in_sublist}>')
            notes_to_html._in_sublist = False
        if in_list:
            html_parts.append(f'</{in_list}>')
            in_list = False
        html_parts.append(f'<p>{inline_md(line)}</p>')
        i += 1

    if getattr(notes_to_html, '_in_sublist', False):
        html_parts.append(f'</{notes_to_html._in_sublist}>')
        notes_to_html._in_sublist = False
    if in_list:
        html_parts.append(f'</{in_list}>')

    return '\n                                    '.join(html_parts)


# ── HTML 生成 ──────────────────────────────────────────────

def render_sm_grid(items):
    """生成 SM 配置 grid HTML"""
    parts = []
    for item in items:
        cls = ' highlight' if item['highlight'] else ''
        parts.append(
            f'<div class="arch-sm-item{cls}">'
            f'<span class="sm-value">{item["value"]}</span>'
            f'<span class="sm-label">{item["label"]}</span>'
            f'</div>'
        )
    return '\n                                    '.join(parts)


def render_figure(arch):
    """生成图片或占位符 HTML"""
    if 'image' in arch:
        caption = arch.get('image_caption', '')
        html = f'<div class="arch-figure">\n'
        html += f'                                <img src="images/{arch["image"]}" alt="{arch["name"]} 架构图">\n'
        if caption:
            html += f'                                <div class="paper-figure-caption">{caption}</div>\n'
        html += f'                            </div>'
        return html
    else:
        return (f'<div class="arch-figure">\n'
                f'                                <div class="arch-figure-placeholder">{arch["name"]} SM 架构图<br>(待补充)</div>\n'
                f'                            </div>')


def render_extra_section(body):
    """渲染额外子段落（如 Volta SIMT、Ampere A100 对比）"""
    lines = body.split('\n')
    html = ''
    i = 0
    text_lines = []

    def flush_text():
        nonlocal html
        if text_lines:
            text_html = notes_to_html('\n'.join(text_lines))
            html += f'                        <div class="arch-notes" style="margin-top:12px">\n'
            html += f'                            {text_html}\n'
            html += f'                        </div>\n'
            text_lines.clear()

    while i < len(lines):
        line = lines[i]

        # 双图
        img2 = re.match(r'^\[images:\s*(.+?)\s*\|\s*(.+?)\s*\]$', line)
        if img2:
            flush_text()
            cap_left, cap_right = '', ''
            if i + 1 < len(lines):
                cap_m = re.match(r'^\[captions:\s*(.+?)\s*\|\s*(.+?)\s*\]$', lines[i + 1])
                if cap_m:
                    cap_left, cap_right = cap_m.group(1).strip(), cap_m.group(2).strip()
                    i += 1
            html += f'                        <div class="arch-content-row">\n'
            html += f'                            <div class="arch-figure-half">\n'
            html += f'                                <img src="images/{img2.group(1).strip()}" alt="{cap_left}">\n'
            if cap_left:
                html += f'                                <div class="paper-figure-caption">{cap_left}</div>\n'
            html += f'                            </div>\n'
            html += f'                            <div class="arch-figure-half">\n'
            html += f'                                <img src="images/{img2.group(2).strip()}" alt="{cap_right}">\n'
            if cap_right:
                html += f'                                <div class="paper-figure-caption">{cap_right}</div>\n'
            html += f'                            </div>\n'
            html += f'                        </div>\n'
            i += 1
            continue

        # 单图
        img1 = re.match(r'^\[image:\s*(.+?)\s*\]$', line)
        if img1:
            flush_text()
            caption = ''
            if i + 1 < len(lines):
                cap_m = re.match(r'^\[caption:\s*(.+?)\s*\]$', lines[i + 1])
                if cap_m:
                    caption = cap_m.group(1).strip()
                    i += 1
            html += f'                        <div class="paper-figure" style="margin-top:12px">\n'
            html += f'                            <img src="images/{img1.group(1).strip()}" alt="{caption}" style="max-width:700px">\n'
            if caption:
                html += f'                            <div class="paper-figure-caption">{caption}</div>\n'
            html += f'                        </div>\n'
            i += 1
            continue

        # 跳过独�� caption
        if re.match(r'^\[captions?:', line):
            i += 1
            continue

        # 普通文本行收集
        text_lines.append(line)
        i += 1

    flush_text()
    return html


def render_card(arch):
    """生成单个架构卡片 HTML"""
    # Tags
    tags = [t.strip() for t in arch.get('tags', '').split(',') if t.strip()]
    tag_html = ''.join(f'\n                            <span class="paper-tag">{t}</span>' for t in tags)

    # SM config
    sm_section = next((s for s in arch['sections'] if s['title'] == 'SM 配置'), None)
    sm_items = parse_sm_config(sm_section['body']) if sm_section else []
    sm_grid = render_sm_grid(sm_items)

    # 说明 section
    notes_section = next((s for s in arch['sections'] if s['title'] == '说明'), None)
    notes_html = notes_to_html(notes_section['body']) if notes_section else ''

    # Figure
    figure_html = render_figure(arch)

    # Extra sections (beyond SM 配置 and 说明)
    extra_sections = [s for s in arch['sections'] if s['title'] not in ('SM 配置', '说明')]
    extra_html = ''
    for sec in extra_sections:
        extra_html += f'\n\n                        <h3 class="arch-sub-title">{arch["name"]} {sec["title"]}</h3>\n'
        extra_html += render_extra_section(sec['body'])

    html = f'''                    <div class="arch-gen" id="{arch['id']}">
                        <div class="arch-gen-header">
                            <h2>{arch['name']}</h2>
                            <span class="paper-tag">{arch['year']}</span>{tag_html}
                        </div>
                        <div class="arch-content-row">
                            <div class="arch-text">
                                <div class="arch-sm-grid">
                                    {sm_grid}
                                </div>
                                <div class="arch-notes">
                                    {notes_html}
                                </div>
                            </div>
                            {figure_html}
                        </div>{extra_html}
                    </div>'''
    return html


def render_toc(archs, compare_title='微架构演进对比'):
    """生成目录 HTML"""
    items = []
    for a in archs:
        items.append(f'                        <li><a href="#{a["id"]}">{a["name"]} ({a["year"]})</a></li>')
    items.insert(0, f'                        <li><a href="#arch-compare">{compare_title}</a></li>')
    return '\n'.join(items)


def render_compare_table(compare_md):
    """将 markdown 表格转为 HTML table"""
    lines = [l.strip() for l in compare_md.strip().split('\n') if l.strip()]
    if len(lines) < 3:
        return ''

    # Header
    headers = [c.strip() for c in lines[0].split('|') if c.strip()]
    # Skip separator line (lines[1])
    # Data rows
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.split('|') if c.strip()]
        rows.append(cells)

    html = '<table class="hardware-matrix">\n'
    html += '                        <thead>\n                            <tr>\n'
    for h in headers:
        html += f'                                <th>{h}</th>\n'
    html += '                            </tr>\n                        </thead>\n'
    html += '                        <tbody>\n'
    for row in rows:
        html += '                            <tr>'
        for j, cell in enumerate(row):
            if j == 0:
                html += f'<td style="text-align:left;font-weight:600">{cell}</td>'
            else:
                html += f'<td>{cell}</td>'
        html += '</tr>\n'
    html += '                        </tbody>\n                    </table>'
    return html


def render_section(archs, compare_md, compare_title='微架构演进对比'):
    """生成完整的 section 内容（不含 <section> 标签本身）"""
    toc_html = render_toc(archs, compare_title)
    cards_html = '\n\n'.join(render_card(a) for a in archs)
    table_html = render_compare_table(compare_md)

    return f'''
                <h1 class="section-title">NVIDIA 微架构演进</h1>

                <h2 class="subsection-title" id="arch-compare">{compare_title}</h2>
                <div class="matrix-container">
                    {table_html}
                </div>

                <div class="page-toc" style="margin-top:24px">
                    <h3>目录</h3>
                    <ul>
{toc_html}
                    </ul>
                </div>

                <div class="arch-timeline" style="margin-top:32px">

{cards_html}

                </div>
            '''


# ── HTML 替换 ──────────────────────────────────────────────

def replace_section(html, new_content):
    """替换 section#nv-arch-overview 的内部内容"""
    # 匹配 <section id="nv-arch-overview" ...> 到对应的 </section>
    pattern = r'(<section id="nv-arch-overview"[^>]*>)(.*?)(</section>)'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        raise RuntimeError('找不到 section#nv-arch-overview')

    return html[:match.start(2)] + new_content + '\n            ' + html[match.end(2):]


# ── 图片同步 ──────────────────────────────────────────────

def sync_images():
    """将 user/images/ 中的图片复制到 web/images/"""
    if not SRC_IMAGES.exists():
        return
    DST_IMAGES.mkdir(exist_ok=True)
    count = 0
    for src in SRC_IMAGES.iterdir():
        if src.is_file():
            dst = DST_IMAGES / src.name
            shutil.copy2(src, dst)
            count += 1
    print(f'  同步 {count} 张图片到 web/images/')


# ── 主流程 ────────────────────────────────────────────────

def main():
    print('读取 user/NV微架构梳理.md ...')
    md_text = MD_FILE.read_text(encoding='utf-8')

    print('解析 markdown ...')
    archs, compare_md, compare_title = parse_md(md_text)
    print(f'  找到 {len(archs)} 个架构')

    print('生成 HTML ...')
    section_html = render_section(archs, compare_md, compare_title)

    print('读取 web/index.html ...')
    html = HTML_FILE.read_text(encoding='utf-8')

    print('替换 NV 微架构 section ...')
    new_html = replace_section(html, section_html)

    print('写回 web/index.html ...')
    HTML_FILE.write_text(new_html, encoding='utf-8')

    print('同步图片 ...')
    sync_images()

    print('完成！')


if __name__ == '__main__':
    main()
