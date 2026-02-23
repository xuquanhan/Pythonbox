from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串，格式为 yyyymmdd 或 yyyy-mm-dd
        
    Returns:
        datetime 对象
    """
    date_str = str(date_str).strip()
    
    for fmt in ['%Y%m%d', '%Y-%m-%d', '%Y/%m/%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期: {date_str}，期望格式为 yyyymmdd 或 yyyy-mm-dd")


def format_date(dt: datetime, fmt: str = '%Y%m%d') -> str:
    """
    格式化日期对象为字符串
    
    Args:
        dt: datetime 对象
        fmt: 输出格式，默认为 yyyymmdd
        
    Returns:
        格式化后的日期字符串
    """
    return dt.strftime(fmt)


def validate_date_range(
    start_date: Optional[str], 
    end_date: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    验证并解析日期范围
    
    Args:
        start_date: 开始日期字符串 (yyyymmdd)
        end_date: 结束日期字符串 (yyyymmdd)
        
    Returns:
        (start_dt, end_dt) 元组
        
    Raises:
        ValueError: 如果日期范围无效
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        start_dt = parse_date(start_date)
    
    if end_date:
        end_dt = parse_date(end_date)
    
    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError(f"开始日期 {start_date} 不能晚于结束日期 {end_date}")
    
    return start_dt, end_dt


def get_date_range_days(start_date: str, end_date: str) -> int:
    """
    计算日期范围的天数
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        天数
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    return (end_dt - start_dt).days + 1


def get_trading_days(start_date: str, end_date: str) -> list:
    """
    获取日期范围内的交易日（排除周末）
    
    注意：此函数仅排除周末，不排除节假日
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        交易日列表
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    
    trading_days = []
    current = start_dt
    
    while current <= end_dt:
        if current.weekday() < 5:
            trading_days.append(current)
        current += timedelta(days=1)
    
    return trading_days
