import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
import time
import base64

from tools.epub_parser import EpubParser
from tools.converter import EpubGenerator, MobiConverter
from tools.translator import translate_epub, Translator

st.set_page_config(
    page_title="EPUB转Mobi翻译工具",
    page_icon="📚",
    layout="wide"
)

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CONVERTED_DIR = DATA_DIR / "converted"
TRANSLATED_DIR = DATA_DIR / "translated"

for d in [RAW_DIR, CONVERTED_DIR, TRANSLATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file) -> str:
    file_path = RAW_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)


def create_download_link(file_path: str, link_text: str = "下载文件"):
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.epub': 'application/epub+zip',
        '.mobi': 'application/x-mobipocket-ebook',
        '.txt': 'text/plain'
    }
    mime = mime_types.get(ext, 'application/octet-stream')
    
    b64 = base64.b64encode(data).decode()
    filename = Path(file_path).name
    return f'<a href="data:{mime};base64,{b64}" download="{filename}">{link_text}</a>'


st.title("📚 EPUB转Mobi翻译工具")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. 上传文件")
    uploaded_file = st.file_uploader(
        "选择文件", 
        type=['epub', 'txt'],
        help="支持上传EPUB或TXT格式的文件"
    )
    
    if uploaded_file:
        st.success(f"已选择: {uploaded_file.name}")
        file_path = save_uploaded_file(uploaded_file)
        file_type = Path(uploaded_file.name).suffix.lower()
        
        st.header("2. 选择操作")
        
        if file_type == '.txt':
            operation = st.radio(
                "操作类型",
                ["仅翻译"],
                help="TXT文件仅支持翻译"
            )
        else:
            operation = st.radio(
                "操作类型",
                ["仅转换格式", "仅翻译", "翻译后转换"],
                help="选择需要执行的操作"
            )
        
        st.header("3. 配置")
        
        if operation != "仅转换格式":
            provider = st.selectbox(
                "翻译服务",
                ["ollama", "dashscope"],
                index=0,
                format_func=lambda x: {
                    "ollama": "Ollama (本地模型，推荐)",
                    "dashscope": "阿里DashScope (云端API)"
                }[x],
                help="Ollama使用本地部署的模型，DashScope调用云端API"
            )
            
            source_lang = st.selectbox(
                "源语言",
                ["auto", "en", "ja", "ko", "fr", "de", "es"],
                format_func=lambda x: {
                    "auto": "自动检测",
                    "en": "英语",
                    "ja": "日语",
                    "ko": "韩语",
                    "fr": "法语",
                    "de": "德语",
                    "es": "西班牙语"
                }[x]
            )
            
            target_lang = st.selectbox(
                "目标语言",
                ["zh", "en", "ja"],
                index=0,
                format_func=lambda x: {
                    "zh": "中文",
                    "en": "英语",
                    "ja": "日语"
                }[x]
            )
        else:
            provider = None
            source_lang = None
            target_lang = None
        
        output_format = st.radio(
            "输出格式",
            ["epub", "txt"],
            format_func=lambda x: {
                "epub": "EPUB格式 (推荐)",
                "txt": "纯文本TXT"
            }[x],
            horizontal=True,
            help="选择输出文件格式"
        )
        
        st.header("4. 开始处理")
        process_btn = st.button("🚀 开始处理", type="primary", use_container_width=True)

with col2:
    st.header("📖 文件信息与结果")
    
    if uploaded_file and process_btn:
        with st.spinner("处理中..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            translate_preview = st.empty()
            
            try:
                status_text.text("正在解析文件...")
                progress_bar.progress(5)
                
                if file_type == '.epub':
                    parser = EpubParser(file_path)
                    result = parser.parse()
                    
                    st.info(f"**书名**: {result['metadata'].get('title', 'Unknown')}")
                    st.info(f"**作者**: {result['metadata'].get('author', 'Unknown')}")
                    st.info(f"**语言**: {result['metadata'].get('language', 'Unknown')}")
                    st.info(f"**章节数**: {len(result['chapters'])}")
                    
                    total_chars = sum(len(ch['content']) for ch in result['chapters'])
                    st.info(f"**总字符数**: {total_chars:,}")
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    st.info(f"**文件名**: {uploaded_file.name}")
                    st.info(f"**字符数**: {len(content):,}")
                
                output_file = None
                
                if operation == "仅转换格式":
                    progress_bar.progress(30)
                    status_text.text("正在转换格式...")
                    
                    converter = MobiConverter()
                    if output_format == "txt":
                        parser = EpubParser(file_path)
                        parser.parse()
                        txt_path = str(CONVERTED_DIR / f"{Path(uploaded_file.name).stem}.txt")
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            for ch in parser.chapters:
                                f.write(f"\n=== {ch['title']} ===\n\n")
                                f.write(ch['content'])
                        output_file = txt_path
                    else:
                        output_file = converter.convert(
                            file_path,
                            str(CONVERTED_DIR / f"{Path(uploaded_file.name).stem}_converted.epub")
                        )
                    
                    progress_bar.progress(100)
                    status_text.text("转换完成!")
                
                elif file_type == '.txt' and operation == "仅翻译":
                    def update_progress(pct, msg):
                        progress_bar.progress(pct)
                        status_text.text(msg)
                    
                    progress_bar.progress(10)
                    status_text.text("正在读取TXT文件...")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    translator = Translator(provider if provider else 'ollama')
                    translator.warm_up()
                    
                    progress_bar.progress(20)
                    status_text.text(f"检测到语言: {source_lang}, 开始翻译...")
                    
                    if source_lang == 'auto':
                        detected_lang = translator.detect_language(content)
                        source_lang = detected_lang
                        status_text.text(f"自动检测为{source_lang}, 开始翻译...")
                    
                    chunks = translator._split_text(content, max_length=1500)
                    translated_parts = []
                    total_chunks = len(chunks)
                    
                    def stream_callback(text):
                        preview_text = '\n\n'.join(translated_parts) + '\n\n' + text
                        translate_preview.text_area("翻译预览", preview_text, height=300)
                    
                    for i, chunk in enumerate(chunks):
                        progress = 20 + int((i + 1) / total_chunks * 60)
                        status_text.text(f"翻译中... ({i+1}/{total_chunks})")
                        translated = translator.translate_text(chunk, source_lang, target_lang, stream_callback=stream_callback if i == 0 else None)
                        translated_parts.append(translated)
                        progress_bar.progress(progress)
                        
                        preview_text = '\n\n'.join(translated_parts)
                        translate_preview.text_area("翻译预览", preview_text, height=300)
                    
                    progress_bar.progress(85)
                    status_text.text("正在保存...")
                    
                    txt_output_path = str(TRANSLATED_DIR / f"[译]{uploaded_file.name}")
                    with open(txt_output_path, 'w', encoding='utf-8') as f:
                        f.write('\n\n'.join(translated_parts))
                    
                    output_file = txt_output_path
                    
                    progress_bar.progress(100)
                    status_text.text("翻译完成!")
                    
                elif operation == "仅翻译":
                    def update_progress(pct, msg):
                        progress_bar.progress(15 + int(pct * 0.7))
                        status_text.text(msg)
                    
                    output_file = translate_epub(
                        file_path,
                        str(TRANSLATED_DIR / f"[译]{uploaded_file.name}"),
                        source_lang=source_lang,
                        target_lang=target_lang,
                        provider=provider,
                        output_format=output_format,
                        progress_callback=update_progress
                    )
                    
                elif operation == "翻译后转换":
                    def update_progress(pct, msg):
                        progress_bar.progress(15 + int(pct * 0.7))
                        status_text.text(msg)
                    
                    temp_epub = translate_epub(
                        file_path,
                        str(TRANSLATED_DIR / f"[译]{uploaded_file.name}"),
                        source_lang=source_lang,
                        target_lang=target_lang,
                        provider=provider,
                        output_format=output_format,
                        progress_callback=update_progress
                    )
                    
                    output_file = temp_epub
                    
                    progress_bar.progress(100)
                    status_text.text("处理完成!")
                
                if output_file and os.path.exists(output_file):
                    st.success(f"✅ 处理完成!")
                    
                    file_size = os.path.getsize(output_file) / 1024 / 1024
                    st.metric("文件大小", f"{file_size:.2f} MB")
                    
                    download_link = create_download_link(output_file, "📥 下载文件")
                    if download_link:
                        st.markdown(download_link, unsafe_allow_html=True)
                else:
                    st.error("处理失败，未能生成输出文件")
                    
            except Exception as e:
                st.error(f"处理出错: {str(e)}")
                import traceback
                with st.expander("查看详细错误"):
                    st.code(traceback.format_exc())
    
    else:
        st.info("👈 请先上传文件并选择操作")
        st.markdown("""
        ### 使用说明
        1. **上传EPUB文件** - 选择要处理的电子书
        2. **选择操作** - 转换格式、翻译或两者同时进行
        3. **配置选项** - 选择源语言和目标语言
        4. **开始处理** - 点击按钮进行处理
        
        ### 支持的功能
        - 📄 EPUB格式转换
        - 🌐 翻译功能（基于阿里Qwen大语言模型）
        - 📱 转换为Mobi格式（Kindle兼容）
        
        ### 注意事项
        - 翻译功能需要配置 DASHSCOPE_API_KEY_QWEN 环境变量
        - 请先复制 .env.example 为 .env 并填入API密钥
        """)

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>EPUB转Mobi翻译工具 v1.0</div>", unsafe_allow_html=True)
