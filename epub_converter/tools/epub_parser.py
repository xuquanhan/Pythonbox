import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
import re


class EpubParser:
    def __init__(self, epub_path: str):
        self.epub_path = Path(epub_path)
        self.temp_dir = None
        self.metadata = {}
        self.chapters = []
        
    def parse(self) -> Dict:
        with zipfile.ZipFile(self.epub_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            container_xml = self._read_xml(zip_ref, 'META-INF/container.xml')
            if container_xml:
                self._parse_container(container_xml)
            
            opf_path = self._find_opf(file_list)
            if opf_path:
                opf_content = self._read_xml(zip_ref, opf_path)
                if opf_content:
                    self._parse_opf(opf_content, zip_ref, opf_path)
        
        return {
            'metadata': self.metadata,
            'chapters': self.chapters
        }
    
    def _read_xml(self, zip_ref, path: str) -> Optional[str]:
        try:
            return zip_ref.read(path).decode('utf-8')
        except:
            return None
    
    def _find_opf(self, file_list: List[str]) -> Optional[str]:
        for f in file_list:
            if f.endswith('.opf'):
                return f
        return None
    
    def _parse_container(self, xml_content: str):
        try:
            root = ET.fromstring(xml_content)
            ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            rootfile = root.find('.//c:rootfile', ns)
            if rootfile is None:
                rootfile = root.find('.//rootfile')
            if rootfile is not None:
                self.opf_path = rootfile.get('full-path')
        except Exception as e:
            print(f"Error parsing container: {e}")
    
    def _parse_opf(self, xml_content: str, zip_ref, opf_path: str):
        try:
            root = ET.fromstring(xml_content)
            
            ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            title = root.find('.//dc:title', ns)
            if title is None:
                title = root.find('.//dc:title')
            self.metadata['title'] = title.text if title is not None else 'Unknown'
            
            creator = root.find('.//dc:creator', ns)
            if creator is None:
                creator = root.find('.//dc:creator')
            self.metadata['author'] = creator.text if creator is not None else 'Unknown'
            
            language = root.find('.//dc:language', ns)
            if language is None:
                language = root.find('.//dc:language')
            self.metadata['language'] = language.text if language is not None else 'en'
            
            manifest = root.find('.//opf:manifest', ns)
            if manifest is None:
                manifest = root.find('.//manifest')
            
            spine = root.find('.//opf:spine', ns)
            if spine is None:
                spine = root.find('.//spine')
            
            if manifest is not None:
                items = {}
                for item in manifest.findall('.//opf:item', ns):
                    if item is None:
                        item = manifest.findall('.//item')[0]
                    id_ = item.get('id')
                    href = item.get('href')
                    media_type = item.get('media-type')
                    items[id_] = {'href': href, 'media_type': media_type}
                
                if spine is not None:
                    for itemref in spine.findall('.//opf:itemref', ns):
                        if itemref is None:
                            continue
                        idref = itemref.get('idref')
                        if idref in items:
                            item = items[idref]
                            if item['media_type'] in ['application/xhtml+xml', 'text/html']:
                                full_path = os.path.join(os.path.dirname(opf_path), item['href'])
                                try:
                                    content = zip_ref.read(full_path).decode('utf-8')
                                    text = self._extract_text(content)
                                    if text.strip():
                                        self.chapters.append({
                                            'title': f"Chapter {len(self.chapters) + 1}",
                                            'content': text
                                        })
                                except:
                                    pass
        except Exception as e:
            print(f"Error parsing OPF: {e}")
    
    def _extract_text(self, html_content: str) -> str:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        return text.strip()
    
    def get_full_text(self) -> str:
        return '\n\n'.join([ch['content'] for ch in self.chapters])
    
    def get_chapters_text(self) -> List[Dict[str, str]]:
        return self.chapters
