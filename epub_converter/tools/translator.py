import os
import re
from typing import List, Dict, Optional, Callable
from dotenv import load_dotenv

load_dotenv()

try:
    import dashscope
    from dashscope import Generation
    dashscope_available = True
except ImportError:
    dashscope_available = False


class Translator:
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY_QWEN')
    
    def translate_text(self, text: str, source_lang: str = 'auto', target_lang: str = 'zh') -> str:
        if not dashscope_available:
            return f"[错误: dashscope库未安装]"
        
        if not self.api_key:
            return f"[错误: 未找到API密钥 DASHSCOPE_API_KEY_QWEN]"
        
        dashscope.api_key = self.api_key
        
        lang_map = {
            'auto': '自动检测',
            'en': '英语',
            'zh': '中文',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语'
        }
        
        source = lang_map.get(source_lang, source_lang)
        target = lang_map.get(target_lang, target_lang)
        
        prompt = f"""请将以下{source}文本翻译成{target}，要求：
1. 保持所有数字、百分比、日期等数据的精确性
2. 使用标准的财经/通用术语
3. 保持自然的中文表达习惯
4. 只返回翻译结果，不要有任何额外解释

原文：
{text}

翻译："""
        
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[
                    {'role': 'system', 'content': '你是一个专业的翻译专家，擅长将各种文本从英文翻译成中文。'},
                    {'role': 'user', 'content': prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                return f"[翻译失败: {response.code}, {response.message}]"
        except Exception as e:
            return f"[翻译错误: {str(e)}]"
    
    def translate_chapters(
        self, 
        chapters: List[Dict[str, str]], 
        source_lang: str = 'auto',
        target_lang: str = 'zh',
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, str]]:
        translated_chapters = []
        total = len(chapters)
        
        for i, chapter in enumerate(chapters):
            title = chapter.get('title', f'Chapter {i+1}')
            content = chapter.get('content', '')
            
            translated_title = self.translate_text(title, source_lang, target_lang)
            
            chunks = self._split_text(content, max_length=4000)
            translated_content = []
            
            for chunk in chunks:
                translated_chunk = self.translate_text(chunk, source_lang, target_lang)
                translated_content.append(translated_chunk)
            
            translated_chapters.append({
                'title': translated_title,
                'content': '\n\n'.join(translated_content)
            })
            
            if progress_callback:
                progress = int((i + 1) / total * 100)
                progress_callback(progress, f"翻译章节: {translated_title}")
        
        return translated_chapters
    
    def _split_text(self, text: str, max_length: int = 4000) -> List[str]:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > max_length and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(para)
            current_length += para_length
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        if not chunks:
            chunks = [text]
        
        return chunks
    
    def detect_language(self, text: str) -> str:
        text = text[:1000]
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        
        if chinese_chars > len(text) * 0.3:
            return 'zh'
        elif japanese_chars > len(text) * 0.2:
            return 'ja'
        elif korean_chars > len(text) * 0.2:
            return 'ko'
        else:
            return 'en'


def translate_epub(
    epub_path: str,
    output_path: str,
    source_lang: str = 'auto',
    target_lang: str = 'zh',
    progress_callback: Optional[Callable] = None
) -> str:
    from tools.epub_parser import EpubParser
    from tools.converter import EpubGenerator
    
    if progress_callback:
        progress_callback(5, "正在解析EPUB文件...")
    
    parser = EpubParser(epub_path)
    parser.parse()
    
    if progress_callback:
        progress_callback(10, "正在检测语言...")
    
    if source_lang == 'auto':
        full_text = parser.get_full_text()
        if full_text:
            translator = Translator()
            source_lang = translator.detect_language(full_text)
    
    if progress_callback:
        progress_callback(15, f"检测到语言: {source_lang}, 开始翻译...")
    
    translator = Translator()
    translated_chapters = translator.translate_chapters(
        parser.chapters,
        source_lang=source_lang,
        target_lang=target_lang,
        progress_callback=progress_callback
    )
    
    if progress_callback:
        progress_callback(85, "正在生成翻译后的EPUB...")
    
    generator = EpubGenerator()
    generator.set_metadata(
        title=f"[译] {parser.metadata.get('title', 'Unknown')}",
        author=parser.metadata.get('author', 'Unknown'),
        language='zh'
    )
    
    for chapter in translated_chapters:
        generator.add_chapter(chapter['title'], chapter['content'])
    
    output_path = generator.generate(output_path)
    
    if progress_callback:
        progress_callback(100, "翻译完成!")
    
    return output_path
