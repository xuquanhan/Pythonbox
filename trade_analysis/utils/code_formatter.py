from typing import Union


def format_security_code(code: Union[str, int, float, None]) -> str:
    """
    格式化证券代码为6位字符串
    
    Args:
        code: 证券代码，可以是字符串、整数或浮点数
        
    Returns:
        6位证券代码字符串，如 "002050"
        
    Examples:
        >>> format_security_code(2050)
        '002050'
        >>> format_security_code("002050")
        '002050'
        >>> format_security_code("2250")
        '002250'
        >>> format_security_code(None)
        ''
    """
    if code is None:
        return ''
    
    code_str = str(code).strip()
    
    if code_str == '' or code_str == 'nan':
        return ''
    
    if '.' in code_str:
        code_str = code_str.split('.')[0]
    
    if code_str.isdigit():
        return code_str.zfill(6)
    
    return code_str


def normalize_user_code(user_input: Union[str, int, float]) -> str:
    """
    标准化用户输入的股票代码
    
    用户可能输入 "002050" 或 "2050" 或 2050，
    此函数统一转换为 "002050" 格式用于匹配
    
    Args:
        user_input: 用户输入的股票代码
        
    Returns:
        6位证券代码字符串
    """
    return format_security_code(user_input)


def is_valid_security_code(code: str) -> bool:
    """
    检查是否为有效的证券代码格式
    
    Args:
        code: 证券代码字符串
        
    Returns:
        True 如果是有效的6位数字代码
    """
    if not code:
        return False
    return len(code) == 6 and code.isdigit()


def get_market_code(code: str) -> str:
    """
    根据证券代码判断市场
    
    Args:
        code: 6位证券代码
        
    Returns:
        市场代码: 'sh' (上海), 'sz' (深圳), 'bj' (北京)
    """
    if not is_valid_security_code(code):
        return ''
    
    prefix = code[:2]
    
    if prefix in ['60', '68']:
        return 'sh'
    elif prefix in ['00', '30']:
        return 'sz'
    elif prefix in ['82', '83', '87', '88']:
        return 'bj'
    else:
        return 'sh'
