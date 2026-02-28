import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import re
import shutil
from datetime import datetime


class EpubGenerator:
    def __init__(self):
        self.metadata = {}
        self.chapters = []
        
    def set_metadata(self, title: str, author: str = 'Unknown', language: str = 'zh'):
        self.metadata = {
            'title': title,
            'author': author,
            'language': language,
            'identifier': f'ebook-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        }
    
    def add_chapter(self, title: str, content: str):
        self.chapters.append({
            'title': title,
            'content': content
        })
    
    def generate(self, output_path: str) -> str:
        output_path = Path(output_path)
        temp_dir = output_path.parent / '.temp_epub'
        
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        try:
            mimetype_path = temp_dir / 'mimetype'
            with open(mimetype_path, 'w', encoding='utf-8') as f:
                f.write('application/epub+zip')
            
            self._create_container(temp_dir)
            self._create_content_opf(temp_dir)
            self._create_toc_ncx(temp_dir)
            self._create_nav(temp_dir)
            self._create_chapters(temp_dir)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            return str(output_path)
            
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _create_container(self, temp_dir: Path):
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        
        meta_inf = temp_dir / 'META-INF'
        meta_inf.mkdir(exist_ok=True)
        
        with open(meta_inf / 'container.xml', 'w', encoding='utf-8') as f:
            f.write(container_xml)
    
    def _create_content_opf(self, temp_dir: Path):
        items = []
        itemrefs = []
        
        for i, chapter in enumerate(self.chapters):
            chapter_id = f'chapter{i}'
            href = f'Text/chapter{i}.xhtml'
            items.append(f'        <item id="{chapter_id}" href="{href}" media-type="application/xhtml+xml"/>')
            itemrefs.append(f'        <itemref idref="{chapter_id}"/>')
        
        items_str = '\n'.join(items)
        itemrefs_str = '\n'.join(itemrefs)
        
        opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{self.metadata.get('title', 'Unknown')}</dc:title>
        <dc:creator>{self.metadata.get('author', 'Unknown')}</dc:creator>
        <dc:language>{self.metadata.get('language', 'zh')}</dc:language>
        <dc:identifier id="BookId" opf:scheme="UUID">{self.metadata.get('identifier', 'unknown')}</dc:identifier>
        <meta name="cover" content="cover-image"/>
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"/>
        <item id="cover-image" href="Images/cover.jpg" media-type="image/jpeg"/>
{items_str}
    </manifest>
    <spine toc="ncx">
{itemrefs_str}
    </spine>
</package>'''
        
        oebps = temp_dir / 'OEBPS'
        oebps.mkdir(exist_ok=True)
        
        with open(oebps / 'content.opf', 'w', encoding='utf-8') as f:
            f.write(opf_content)
    
    def _create_toc_ncx(self, temp_dir: Path):
        nav_points = []
        for i, chapter in enumerate(self.chapters):
            nav_points.append(f'''        <navPoint id="navPoint{i+1}" playOrder="{i+1}">
            <navLabel>
                <text>{self._escape_xml(chapter['title'])}</text>
            </navLabel>
            <content src="Text/chapter{i}.xhtml"/>
        </navPoint>''')
        
        nav_points_str = '\n'.join(nav_points)
        
        ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{self.metadata.get('identifier', 'unknown')}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{self._escape_xml(self.metadata.get('title', 'Unknown'))}</text>
    </docTitle>
    <navMap>
{nav_points_str}
    </navMap>
</ncx>'''
        
        with open(temp_dir / 'OEBPS' / 'toc.ncx', 'w', encoding='utf-8') as f:
            f.write(ncx_content)
    
    def _create_nav(self, temp_dir: Path):
        nav_items = []
        for i, chapter in enumerate(self.chapters):
            nav_items.append(f'            <li><a href="Text/chapter{i}.xhtml">{self._escape_xml(chapter['title'])}</a></li>')
        
        nav_items_str = '\n'.join(nav_items)
        
        nav_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Table of Contents</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>目录</h1>
    <nav type="toc">
        <ul>
{nav_items_str}
        </ul>
    </nav>
</body>
</html>'''
        
        with open(temp_dir / 'OEBPS' / 'nav.xhtml', 'w', encoding='utf-8') as f:
            f.write(nav_content)
    
    def _create_chapters(self, temp_dir: Path):
        text_dir = temp_dir / 'OEBPS' / 'Text'
        text_dir.mkdir(exist_ok=True)
        
        images_dir = temp_dir / 'OEBPS' / 'Images'
        images_dir.mkdir(exist_ok=True)
        
        placeholder_jpg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x27 ,#\x1c\x1c(7),01444\x1f\x27;=0<->?7<]4:MQVBGIRJDEH>CLP^_a\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\x00\xff\xd9'
        
        with open(images_dir / 'cover.jpg', 'wb') as f:
            f.write(placeholder_jpg)
        
        for i, chapter in enumerate(self.chapters):
            chapter_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{self._escape_xml(chapter['title'])}</title>
    <style>
        body {{ font-family: "Times New Roman", serif; font-size: 12pt; line-height: 1.6; margin: 1in; }}
        h1 {{ font-size: 18pt; text-align: center; margin-bottom: 1em; }}
    </style>
</head>
<body>
    <h1>{self._escape_xml(chapter['title'])}</h1>
    <p>{self._escape_xml(chapter['content'])}</p>
</body>
</html>'''
            
            with open(text_dir / f'chapter{i}.xhtml', 'w', encoding='utf-8') as f:
                f.write(chapter_content)
    
    def _escape_xml(self, text: str) -> str:
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


class MobiConverter:
    def __init__(self):
        self.epub_path = None
        self.output_path = None
    
    def convert(self, epub_path: str, output_path: str = None) -> str:
        from tools.epub_parser import EpubParser
        
        parser = EpubParser(epub_path)
        parser.parse()
        
        generator = EpubGenerator()
        generator.set_metadata(
            title=parser.metadata.get('title', 'Translated'),
            author=parser.metadata.get('author', 'Unknown'),
            language='zh'
        )
        
        for chapter in parser.chapters:
            generator.add_chapter(chapter['title'], chapter['content'])
        
        if output_path is None:
            output_path = epub_path.replace('.epub', '_converted.epub')
        
        generator.generate(output_path)
        return output_path
    
    def convert_to_mobi(self, epub_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = epub_path.replace('.epub', '.mobi')
        
        epub_converted = self.convert(epub_path, output_path.replace('.mobi', '.epub'))
        
        try:
            import subprocess
            
            result = subprocess.run(
                ['ebook-convert', epub_converted, output_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                return output_path
            elif Path(epub_converted).exists():
                return epub_converted
            else:
                return epub_converted
        except FileNotFoundError:
            return epub_converted
        except Exception as e:
            print(f"Mobi conversion error: {e}")
            return epub_converted
