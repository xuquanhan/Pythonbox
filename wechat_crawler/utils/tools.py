#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块

包含各种通用工具函数，如时间处理、文本处理、文件操作等
"""

import os
import re
import time
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

def ensure_directory(path: str):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)

def load_config(config_path: str) -> Optional[Dict]:
    """加载配置文件"""
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif config_path.endswith('.json'):
                return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {str(e)}")
    return None

def save_config(config: Dict, config_path: str):
    """保存配置文件"""
    try:
        ensure_directory(os.path.dirname(config_path))
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            elif config_path.endswith('.json'):
                json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {str(e)}")
        return False

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化日期时间"""
    return dt.strftime(format_str)

def parse_datetime(date_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """解析日期时间字符串"""
    try:
        return datetime.strptime(date_str, format_str)
    except Exception:
        return None

def get_current_time() -> str:
    """获取当前时间字符串"""
    return format_datetime(datetime.now())

def calculate_time_diff(start_time: str, end_time: str) -> Dict[str, int]:
    """计算时间差"""
    start = parse_datetime(start_time)
    end = parse_datetime(end_time)
    
    if not start or not end:
        return {}
    
    delta = end - start
    return {
        'days': delta.days,
        'hours': delta.seconds // 3600,
        'minutes': (delta.seconds % 3600) // 60,
        'seconds': delta.seconds % 60
    }

def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ''
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    text = text.strip()
    return text

def validate_url(url: str) -> bool:
    """验证URL"""
    pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(pattern.match(url))

def extract_domain(url: str) -> Optional[str]:
    """提取域名"""
    pattern = re.compile(r'^(?:http|ftp)s?://([^/]+)', re.IGNORECASE)
    match = pattern.match(url)
    return match.group(1) if match else None

def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """读取文件"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        return None

def write_file(content: str, file_path: str, encoding: str = 'utf-8'):
    """写入文件"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文件失败: {str(e)}")
        return False

def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    filename = filename[:255]
    return filename

def batch_process(items: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """批量处理列表"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i+batch_size])
    return batches

def retry(func, max_attempts: int = 3, delay: int = 1, exceptions: tuple = (Exception,)):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                attempts += 1
                if attempts >= max_attempts:
                    raise
                time.sleep(delay * attempts)
        return func(*args, **kwargs)
    return wrapper

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """将列表分块"""
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """扁平化字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d: Dict, sep: str = '_') -> Dict:
    """反扁平化字典"""
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = v
    return result

def deep_get(d: Dict, keys: List[str], default: Any = None) -> Any:
    """深度获取字典值"""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d

def deep_set(d: Dict, keys: List[str], value: Any):
    """深度设置字典值"""
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[keys[-1]] = value

def merge_dicts(*dicts: Dict) -> Dict:
    """合并字典"""
    result = {}
    for d in dicts:
        result.update(d)
    return result

def is_empty(value: Any) -> bool:
    """检查值是否为空"""
    if value is None:
        return True
    if isinstance(value, str):
        return len(value.strip()) == 0
    if isinstance(value, (list, dict, set, tuple)):
        return len(value) == 0
    return False

def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-len(suffix)] + suffix

def normalize_string(s: str) -> str:
    """标准化字符串"""
    if not s:
        return ''
    # 移除零宽字符
    s = re.sub(r'[\u200B-\u200D\uFEFF]', '', s)
    # 统一空白字符
    s = re.sub(r'\s+', ' ', s)
    return s.strip()
