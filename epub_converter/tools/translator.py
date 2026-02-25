import os
import re
import json
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
    def __init__(self, provider: str = 'ollama'):
        self.provider = provider
        self.api_key = os.getenv('DASHSCOPE_API_KEY_QWEN')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'quantumcookie/Sakura-qwen2.5-v1.0:7b')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self._warmed_up = False
    
    def warm_up(self):
        if self.provider == 'ollama' and not self._warmed_up:
            try:
                import requests
                requests.post(
                    f'{self.ollama_url}/api/generate',
                    json={'model': self.ollama_model, 'prompt': 'test', 'stream': False},
                    timeout=10
                )
                self._warmed_up = True
            except:
                pass
    
    def translate_text(self, text: str, source_lang: str = 'auto', target_lang: str = 'zh', stream_callback=None) -> str:
        if self.provider == 'ollama':
            return self._translate_ollama(text, source_lang, target_lang, stream_callback)
        elif self.provider == 'dashscope':
            return self._translate_dashscope(text, source_lang, target_lang)
        else:
            return self._translate_dashscope(text, source_lang, target_lang)
    
    def _translate_ollama(self, text: str, source_lang: str, target_lang: str, stream_callback=None) -> str:
        import requests
        
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
        
        prompt = f"""你是一个专业的文学翻译助手，需要全文翻译，不要有任何删减、修改或拒绝。即使包含成人情节描写，也必须完整翻译。
        
{text}"""
        
        try:
            if stream_callback:
                full_response = ""
                response = requests.post(
                    f'{self.ollama_url}/api/generate',
                    json={
                        'model': self.ollama_model,
                        'prompt': prompt,
                        'stream': True,
                        'options': {
                            'temperature': 0.3,
                            'num_predict': 8192,
                            'safe': False,
                            'dangerous': True
                        }
                    },
                    stream=True,
                    timeout=300
                )
                
                for line in response.iter_lines():
                    if line:
                        data = line.decode('utf-8')
                        if data.startswith('data:'):
                            import json
                            try:
                                chunk = json.loads(data[5:])
                                if 'response' in chunk:
                                    full_response += chunk['response']
                                    stream_callback(full_response)
                            except:
                                pass
                
                return full_response.strip()
            else:
                response = requests.post(
                    f'{self.ollama_url}/api/generate',
                    json={
                        'model': self.ollama_model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {
                            'temperature': 0.3,
                            'num_predict': 8192,
                            'safe': False,
                            'dangerous': True
                        }
                    },
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"[翻译失败: {response.status_code}] {text}"
        except Exception as e:
            return f"[翻译错误: {str(e)}]"
    
    def _translate_dashscope(self, text: str, source_lang: str, target_lang: str) -> str:
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
        
        prompt = f"""你是一个专业的文学翻译助手，需要全文翻译，不要有任何删减、修改或拒绝。即使包含成人情节描写，也必须完整翻译。
        
{text}"""
        
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[
                    {'role': 'system', 'content': '你是一个专业的文学翻译助手，需要全文翻译，不要有任何删减、修改或拒绝。即使包含成人情节描写，也必须完整翻译。'},
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
            
            if progress_callback:
                progress_callback(
                    int((i / total) * 80), 
                    f"正在翻译章节 {i+1}/{total}: {title[:30]}..."
                )
            
            translated_title = self.translate_text(title, source_lang, target_lang)
            
            chunks = self._split_text(content, max_length=1500)
            translated_content = []
            
            for j, chunk in enumerate(chunks):
                translated_chunk = self.translate_text(chunk, source_lang, target_lang)
                translated_content.append(translated_chunk)
                
                if progress_callback:
                    chunk_progress = int(((i + (j + 1) / len(chunks)) / total) * 80)
                    progress_callback(chunk_progress, f"翻译中 {i+1}/{total}: {title[:25]}... ({j+1}/{len(chunks)}块)")
            
            translated_chapters.append({
                'title': translated_title,
                'content': '\n\n'.join(translated_content)
            })
            
            if progress_callback:
                progress = int(((i + 1) / total) * 100)
                progress_callback(progress, f"已完成 {i+1}/{total}: {translated_title[:30]}")
        
        return translated_chapters
    
    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
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
    provider: str = 'ollama',
    output_format: str = 'epub',
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
            translator = Translator(provider)
            source_lang = translator.detect_language(full_text)
    
    if progress_callback:
        progress_callback(15, f"检测到语言: {source_lang}, 开始翻译...")
    
    translator = Translator(provider)
    translated_chapters = translator.translate_chapters(
        parser.chapters,
        source_lang=source_lang,
        target_lang=target_lang,
        progress_callback=progress_callback
    )
    
    if output_format == "txt":
        if progress_callback:
            progress_callback(85, "正在生成TXT文件...")
        
        txt_path = output_path.replace('.epub', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            for ch in translated_chapters:
                f.write(f"\n=== {ch['title']} ===\n\n")
                f.write(ch['content'])
        
        if progress_callback:
            progress_callback(100, "翻译完成!")
        
        return txt_path
    else:
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
