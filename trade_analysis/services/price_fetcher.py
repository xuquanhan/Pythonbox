"""
股票价格获取模块

支持多数据源（按优先级）：
1. Wind API
2. Bloomberg API
3. Refinitiv Workspace API
4. AkShare (免费备选)

使用方法:
    fetcher = PriceFetcher()
    price = fetcher.get_latest_price('000001')
    history = fetcher.get_history_prices('000001', '20230101', '20231231')
"""

import pandas as pd
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class PriceFetchError(Exception):
    """价格获取异常"""
    pass


class DataSourceConfig:
    """数据源配置"""
    
    def __init__(self):
        self.wind_enabled = True
        self.bloomberg_enabled = True
        self.workspace_enabled = True
        self.akshare_enabled = True
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        
        # 超时配置
        self.timeout = 30  # 秒


class PriceFetcher:
    """
    股票价格获取器
    
    支持多数据源，按优先级尝试获取价格
    
    Attributes:
        config: 数据源配置
        _wind_available: Wind API 是否可用
        _bloomberg_available: Bloomberg API 是否可用
        _workspace_available: Workspace API 是否可用
        _akshare_available: AkShare 是否可用
    """
    
    def __init__(self, config: Optional[DataSourceConfig] = None):
        """
        初始化价格获取器
        
        Args:
            config: 数据源配置，如果为 None 则使用默认配置
        """
        self.config = config or DataSourceConfig()
        
        self._wind_available = False
        self._bloomberg_available = False
        self._workspace_available = False
        self._akshare_available = False
        
        self._wind_conn = None
        
        # 初始化各数据源
        self._init_wind()
        self._init_bloomberg()
        self._init_workspace()
        self._init_akshare()
        
        logger.info(f"价格获取器初始化完成，可用数据源: {self.get_available_sources()}")
    
    def _init_wind(self) -> None:
        """初始化 Wind API"""
        if not self.config.wind_enabled:
            logger.info("Wind API 已禁用")
            return
            
        try:
            import WindPy
            
            # 启动 Wind API 连接
            WindPy.w.start()
            
            # 检查连接状态
            if WindPy.w.isconnected():
                # 进一步测试：尝试获取一个测试数据
                try:
                    test_result = WindPy.w.wsd("000001.SZ", "close", "20240101", "20240101", "")
                    if test_result.ErrorCode == 0 and test_result.Data and len(test_result.Data) > 0:
                        self._wind_available = True
                        self._wind_conn = WindPy.w
                        logger.info("Wind API 连接成功")
                    else:
                        logger.warning(f"Wind API 连接测试失败: {test_result.Data}")
                except Exception as test_e:
                    logger.warning(f"Wind API 连接测试失败: {test_e}")
            else:
                logger.warning("Wind API 连接失败，请确保 Wind 终端已启动")
                
        except ImportError:
            logger.warning("WindPy 未安装，Wind API 不可用")
        except Exception as e:
            logger.warning(f"Wind API 初始化失败: {e}")
    
    def _init_bloomberg(self) -> None:
        """初始化 Bloomberg API"""
        if not self.config.bloomberg_enabled:
            logger.info("Bloomberg API 已禁用")
            return
            
        try:
            import blpapi
            
            # 尝试连接 Bloomberg 终端
            options = blpapi.SessionOptions()
            options.setServerHost("localhost")
            options.setServerPort(8194)
            
            session = blpapi.Session(options)
            if session.start():
                # 连接成功，测试打开服务
                if session.openService("//blp/refdata"):
                    self._bloomberg_available = True
                    self._bloomberg_session = session
                    logger.info("Bloomberg API 连接成功")
                else:
                    session.stop()
                    self._bloomberg_available = False
                    logger.warning("Bloomberg API 连接成功但无法打开服务")
            else:
                self._bloomberg_available = False
                logger.warning("Bloomberg API 连接失败，请确保 Bloomberg 终端已启动")
                
        except ImportError:
            logger.warning("blpapi 未安装，Bloomberg API 不可用")
            self._bloomberg_available = False
        except Exception as e:
            logger.warning(f"Bloomberg API 初始化失败: {e}")
            self._bloomberg_available = False
    
    def _init_workspace(self) -> None:
        """初始化 Refinitiv Workspace API"""
        if not self.config.workspace_enabled:
            logger.info("Refinitiv Workspace API 已禁用")
            return
            
        try:
            import refinitiv.data as rd
            rd.open_session()
            self._workspace_available = True
            logger.info("Refinitiv Workspace API 可用")
        except ImportError:
            logger.warning("refinitiv.data 未安装，Workspace API 不可用")
        except Exception as e:
            logger.warning(f"Refinitiv Workspace API 初始化失败: {e}")
    
    def _init_akshare(self) -> None:
        """初始化 AkShare"""
        if not self.config.akshare_enabled:
            logger.info("AkShare 已禁用")
            return
            
        try:
            import akshare as ak
            self._akshare_available = True
            logger.info("AkShare 可用")
        except ImportError:
            logger.warning("akshare 未安装，AkShare 不可用")
    
    def _normalize_code(self, code: str) -> str:
        """
        标准化股票代码
        
        Args:
            code: 原始股票代码
            
        Returns:
            标准化后的6位代码
        """
        code = str(code).strip()
        # 移除后缀
        if '.' in code:
            code = code.split('.')[0]
        # 确保6位
        code = code.zfill(6)
        return code
    
    def _get_exchange(self, code: str) -> str:
        """
        根据代码判断交易所
        
        Args:
            code: 股票代码
            
        Returns:
            交易所代码 (SH/SZ/BJ)
        """
        code = self._normalize_code(code)
        if code.startswith('6') or code.startswith('68'):
            return 'SH'
        elif code.startswith('0') or code.startswith('3'):
            return 'SZ'
        elif code.startswith('8') or code.startswith('4'):
            return 'BJ'
        return 'SH'
    
    def _get_wind_code(self, code: str) -> str:
        """
        获取 Wind 代码格式
        
        Args:
            code: 股票代码
            
        Returns:
            Wind 代码格式 (如 000001.SZ)
        """
        exchange = self._get_exchange(code)
        return f"{code}.{exchange}"
    
    def get_latest_price(self, code: str) -> Optional[float]:
        """
        获取最新价格
        
        按优先级尝试各数据源：Wind -> Bloomberg -> Workspace -> AkShare
        
        Args:
            code: 股票代码
            
        Returns:
            最新价格，失败返回 None
            
        Raises:
            PriceFetchError: 所有数据源都失败时抛出
        """
        code = self._normalize_code(code)
        errors = []
        
        # 1. 尝试 Wind
        if self._wind_available:
            try:
                price = self._get_price_from_wind(code)
                if price is not None and not pd.isna(price):
                    logger.debug(f"从 Wind 获取 {code} 价格成功: {price}")
                    return price
            except Exception as e:
                errors.append(f"Wind: {e}")
                logger.debug(f"Wind 获取 {code} 价格失败: {e}")
        
        # 2. 尝试 Bloomberg
        if self._bloomberg_available:
            try:
                price = self._get_price_from_bloomberg(code)
                if price is not None and not pd.isna(price):
                    logger.debug(f"从 Bloomberg 获取 {code} 价格成功: {price}")
                    return price
            except Exception as e:
                errors.append(f"Bloomberg: {e}")
                logger.debug(f"Bloomberg 获取 {code} 价格失败: {e}")
        
        # 3. 尝试 Workspace
        if self._workspace_available:
            try:
                price = self._get_price_from_workspace(code)
                if price is not None and not pd.isna(price):
                    logger.debug(f"从 Workspace 获取 {code} 价格成功: {price}")
                    return price
            except Exception as e:
                errors.append(f"Workspace: {e}")
                logger.debug(f"Workspace 获取 {code} 价格失败: {e}")
        
        # 4. 尝试 AkShare
        if self._akshare_available:
            try:
                price = self._get_price_from_akshare(code)
                if price is not None and not pd.isna(price):
                    logger.debug(f"从 AkShare 获取 {code} 价格成功: {price}")
                    return price
            except Exception as e:
                errors.append(f"AkShare: {e}")
                logger.debug(f"AkShare 获取 {code} 价格失败: {e}")
        
        error_msg = f"无法获取 {code} 的价格。错误: {'; '.join(errors)}"
        logger.error(error_msg)
        return None
    
    def get_history_prices(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取历史价格
        
        按优先级尝试各数据源：Wind -> Bloomberg -> Workspace -> AkShare
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            DataFrame 包含 date, open, high, low, close, volume 列
            失败返回 None
        """
        code = self._normalize_code(code)
        errors = []
        
        # 1. 尝试 Wind
        if self._wind_available:
            try:
                prices = self._get_history_from_wind(code, start_date, end_date)
                if prices is not None and not prices.empty:
                    logger.debug(f"从 Wind 获取 {code} 历史价格成功")
                    return prices
            except Exception as e:
                errors.append(f"Wind: {e}")
                logger.debug(f"Wind 获取 {code} 历史价格失败: {e}")
        
        # 2. 尝试 Bloomberg
        if self._bloomberg_available:
            try:
                prices = self._get_history_from_bloomberg(code, start_date, end_date)
                if prices is not None and not prices.empty:
                    logger.debug(f"从 Bloomberg 获取 {code} 历史价格成功")
                    return prices
            except Exception as e:
                errors.append(f"Bloomberg: {e}")
                logger.debug(f"Bloomberg 获取 {code} 历史价格失败: {e}")
        
        # 3. 尝试 Workspace
        if self._workspace_available:
            try:
                prices = self._get_history_from_workspace(code, start_date, end_date)
                if prices is not None and not prices.empty:
                    logger.debug(f"从 Workspace 获取 {code} 历史价格成功")
                    return prices
            except Exception as e:
                errors.append(f"Workspace: {e}")
                logger.debug(f"Workspace 获取 {code} 历史价格失败: {e}")
        
        # 4. 尝试 AkShare
        if self._akshare_available:
            try:
                prices = self._get_history_from_akshare(code, start_date, end_date)
                if prices is not None and not prices.empty:
                    logger.debug(f"从 AkShare 获取 {code} 历史价格成功")
                    return prices
            except Exception as e:
                errors.append(f"AkShare: {e}")
                logger.debug(f"AkShare 获取 {code} 历史价格失败: {e}")
        
        error_msg = f"无法获取 {code} 的历史价格。错误: {'; '.join(errors)}"
        logger.error(error_msg)
        return None
    
    def _get_price_from_wind(self, code: str) -> Optional[float]:
        """从 Wind 获取最新价格"""
        if not self._wind_available or self._wind_conn is None:
            return None
            
        wind_code = self._get_wind_code(code)
        
        # 重试机制
        for attempt in range(self.config.max_retries):
            try:
                result = self._wind_conn.wsq(wind_code, "rt_last")
                
                if result.ErrorCode == 0 and result.Data and len(result.Data) > 0:
                    price = result.Data[0][0]
                    if price is not None and price > 0:
                        return float(price)
                    elif price == 0:
                        # 实时价格为0，可能是休市或停牌，尝试获取最近收盘价
                        logger.debug(f"Wind 获取 {code} 实时价格为0，尝试获取最近收盘价")
                        from datetime import datetime, timedelta
                        end_date = datetime.now().strftime("%Y-%m-%d")
                        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                        hist_result = self._wind_conn.wsd(wind_code, "close", start_date, end_date)
                        if hist_result.ErrorCode == 0 and hist_result.Data and len(hist_result.Data) > 0:
                            # 获取最后一个非零价格
                            for price in reversed(hist_result.Data[0]):
                                if price is not None and price > 0:
                                    logger.debug(f"Wind 获取 {code} 最近收盘价: {price}")
                                    return float(price)
                
                logger.debug(f"Wind 获取 {code} 价格返回空数据，重试 {attempt + 1}/{self.config.max_retries}")
                
            except Exception as e:
                logger.debug(f"Wind 获取 {code} 价格异常: {e}")
            
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay)
        
        return None
    
    def _get_history_from_wind(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 Wind 获取历史价格"""
        if not self._wind_available or self._wind_conn is None:
            return None
            
        wind_code = self._get_wind_code(code)
        
        # 转换日期格式
        start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        # 重试机制
        for attempt in range(self.config.max_retries):
            try:
                result = self._wind_conn.wsd(
                    wind_code, 
                    "open,high,low,close,volume", 
                    start, 
                    end
                )
                
                if result.ErrorCode == 0 and result.Data and len(result.Data) == 5:
                    df = pd.DataFrame({
                        'date': result.Times,
                        'open': result.Data[0],
                        'high': result.Data[1],
                        'low': result.Data[2],
                        'close': result.Data[3],
                        'volume': result.Data[4]
                    })
                    
                    # 数据验证
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.dropna(subset=['close'])
                    
                    if not df.empty:
                        return df
                
                logger.debug(f"Wind 获取 {code} 历史价格返回空数据，重试 {attempt + 1}/{self.config.max_retries}")
                
            except Exception as e:
                logger.debug(f"Wind 获取 {code} 历史价格异常: {e}")
            
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay)
        
        return None
    
    def _get_price_from_bloomberg(self, code: str) -> Optional[float]:
        """从 Bloomberg 获取最新价格"""
        try:
            import blpapi
            
            # 构建 Bloomberg 证券代码
            exchange = self._get_exchange(code)
            if exchange == 'SH':
                ticker = f"{code} CH Equity"
            elif exchange == 'SZ':
                ticker = f"{code} CH Equity"
            else:
                ticker = f"{code} CH Equity"
            
            # 设置连接选项
            options = blpapi.SessionOptions()
            options.setServerHost("localhost")
            options.setServerPort(8194)
            
            # 创建并启动会话
            session = blpapi.Session(options)
            if not session.start():
                logger.debug("Bloomberg 会话启动失败")
                return None
            
            try:
                # 打开参考数据服务
                if not session.openService("//blp/refdata"):
                    logger.debug("Bloomberg 无法打开 refdata 服务")
                    return None
                
                service = session.getService("//blp/refdata")
                
                # 创建请求
                request = service.createRequest("ReferenceDataRequest")
                request.getElement("securities").appendValue(ticker)
                request.getElement("fields").appendValue("PX_LAST")
                
                # 发送请求
                session.sendRequest(request)
                
                # 等待响应
                while True:
                    event = session.nextEvent(5000)
                    
                    for msg in event:
                        if event.eventType() == blpapi.Event.RESPONSE:
                            security_data = msg.getElement("securityData")
                            for i in range(security_data.numValues()):
                                security = security_data.getValueAsElement(i)
                                field_data = security.getElement("fieldData")
                                if field_data.hasElement("PX_LAST"):
                                    price = field_data.getElementAsFloat("PX_LAST")
                                    if price > 0:
                                        return price
                            return None
                    
                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                        
            finally:
                session.stop()
                
        except Exception as e:
            logger.debug(f"Bloomberg 获取 {code} 价格失败: {e}")
        
        return None
    
    def _get_history_from_bloomberg(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 Bloomberg 获取历史价格"""
        try:
            import blpapi
            
            # 构建 Bloomberg 证券代码
            exchange = self._get_exchange(code)
            if exchange == 'SH':
                ticker = f"{code} CH Equity"
            elif exchange == 'SZ':
                ticker = f"{code} CH Equity"
            else:
                ticker = f"{code} CH Equity"
            
            # 转换日期格式
            start = f"{start_date[:4]}{start_date[4:6]}{start_date[6:]}"
            end = f"{end_date[:4]}{end_date[4:6]}{end_date[6:]}"
            
            # 设置连接选项
            options = blpapi.SessionOptions()
            options.setServerHost("localhost")
            options.setServerPort(8194)
            
            # 创建并启动会话
            session = blpapi.Session(options)
            if not session.start():
                logger.debug("Bloomberg 会话启动失败")
                return None
            
            try:
                # 打开参考数据服务
                if not session.openService("//blp/refdata"):
                    logger.debug("Bloomberg 无法打开 refdata 服务")
                    return None
                
                service = session.getService("//blp/refdata")
                
                # 创建历史数据请求
                request = service.createRequest("HistoricalDataRequest")
                request.getElement("securities").appendValue(ticker)
                request.getElement("fields").appendValue("OPEN")
                request.getElement("fields").appendValue("HIGH")
                request.getElement("fields").appendValue("LOW")
                request.getElement("fields").appendValue("PX_LAST")
                request.getElement("fields").appendValue("VOLUME")
                request.set("periodicityAdjustment", "ACTUAL")
                request.set("periodicitySelection", "DAILY")
                request.set("startDate", start)
                request.set("endDate", end)
                
                # 发送请求
                session.sendRequest(request)
                
                # 收集响应数据
                data_list = []
                
                while True:
                    event = session.nextEvent(5000)
                    
                    for msg in event:
                        if event.eventType() == blpapi.Event.RESPONSE or \
                           event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                            security_data = msg.getElement("securityData")
                            for i in range(security_data.numValues()):
                                security = security_data.getValueAsElement(i)
                                field_data = security.getElement("fieldData")
                                
                                for j in range(field_data.numValues()):
                                    date_data = field_data.getValueAsElement(j)
                                    date_str = date_data.getElementAsString("date")
                                    
                                    try:
                                        row = {
                                            'date': pd.to_datetime(date_str),
                                            'open': date_data.getElementAsFloat("OPEN") if date_data.hasElement("OPEN") else None,
                                            'high': date_data.getElementAsFloat("HIGH") if date_data.hasElement("HIGH") else None,
                                            'low': date_data.getElementAsFloat("LOW") if date_data.hasElement("LOW") else None,
                                            'close': date_data.getElementAsFloat("PX_LAST") if date_data.hasElement("PX_LAST") else None,
                                            'volume': date_data.getElementAsInt64("VOLUME") if date_data.hasElement("VOLUME") else None
                                        }
                                        data_list.append(row)
                                    except:
                                        pass
                    
                    if event.eventType() == blpapi.Event.RESPONSE:
                        break
                
                if data_list:
                    df = pd.DataFrame(data_list)
                    df = df.dropna(subset=['close'])
                    if not df.empty:
                        return df
                        
            finally:
                session.stop()
                
        except Exception as e:
            logger.debug(f"Bloomberg 获取 {code} 历史价格失败: {e}")
        
        return None
    
    def _get_price_from_workspace(self, code: str) -> Optional[float]:
        """从 Refinitiv Workspace 获取最新价格"""
        try:
            import refinitiv.data as rd
            
            exchange = self._get_exchange(code)
            ric = f"{code}.{exchange}"
            
            price = rd.get_data(ric, fields=["TR.PriceClose"])
            
            if price is not None and not price.empty:
                value = price.iloc[0, 0]
                if value is not None and value > 0:
                    return float(value)
                    
        except Exception as e:
            logger.debug(f"Workspace 获取 {code} 价格失败: {e}")
        
        return None
    
    def _get_history_from_workspace(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 Refinitiv Workspace 获取历史价格"""
        try:
            import refinitiv.data as rd
            
            exchange = self._get_exchange(code)
            ric = f"{code}.{exchange}"
            
            # 转换日期格式
            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            df = rd.get_history(
                ric, 
                start=start, 
                end=end, 
                fields=["OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]
            )
            
            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
                df['date'] = pd.to_datetime(df['date'])
                df = df.dropna(subset=['close'])
                
                if not df.empty:
                    return df
                    
        except Exception as e:
            logger.debug(f"Workspace 获取 {code} 历史价格失败: {e}")
        
        return None
    
    def _get_price_from_akshare(self, code: str) -> Optional[float]:
        """从 AkShare 获取最新价格"""
        try:
            import akshare as ak
            
            exchange = self._get_exchange(code)
            
            if exchange == 'SH':
                df = ak.stock_sh_a_spot_em()
                stock = df[df['代码'] == code]
            else:
                df = ak.stock_sz_a_spot_em()
                stock = df[df['代码'] == code]
            
            if not stock.empty:
                price = stock.iloc[0]['最新价']
                if price is not None and price > 0:
                    return float(price)
                    
        except Exception as e:
            logger.debug(f"AkShare 获取 {code} 价格失败: {e}")
        
        return None
    
    def _get_history_from_akshare(
        self, 
        code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """从 AkShare 获取历史价格"""
        try:
            import akshare as ak
            
            # 转换日期格式
            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            df = ak.stock_zh_a_hist(
                symbol=code, 
                period="daily", 
                start_date=start, 
                end_date=end, 
                adjust="qfq"
            )
            
            if df is not None and not df.empty:
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '最高': 'high',
                    '最低': 'low',
                    '收盘': 'close',
                    '成交量': 'volume'
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df.dropna(subset=['close'])
                
                if not df.empty:
                    return df[['date', 'open', 'high', 'low', 'close', 'volume']]
                    
        except Exception as e:
            logger.debug(f"AkShare 获取 {code} 历史价格失败: {e}")
        
        return None
    
    def get_available_sources(self) -> List[str]:
        """
        获取可用的数据源列表
        
        Returns:
            可用数据源名称列表
        """
        sources = []
        if self._wind_available:
            sources.append("Wind")
        if self._bloomberg_available:
            sources.append("Bloomberg")
        if self._workspace_available:
            sources.append("Refinitiv Workspace")
        if self._akshare_available:
            sources.append("AkShare")
        return sources
    
    def check_source_availability(self) -> Dict[str, Dict]:
        """
        检查各数据源的实际可用性
        
        按优先级测试每个数据源是否能成功获取数据
        
        Returns:
            字典，包含每个数据源的状态信息:
            {
                'Wind': {'initialized': True, 'test_passed': False, 'error': '...'},
                'Bloomberg': {...},
                ...
            }
        """
        test_code = '000001'  # 平安银行作为测试代码
        results = {}
        
        # 1. 检查 Wind
        if self._wind_available:
            try:
                price = self._get_price_from_wind(test_code)
                results['Wind'] = {
                    'initialized': True,
                    'test_passed': price is not None and price > 0,
                    'error': None if price is not None and price > 0 else '无法获取测试数据'
                }
            except Exception as e:
                results['Wind'] = {
                    'initialized': True,
                    'test_passed': False,
                    'error': str(e)
                }
        else:
            results['Wind'] = {'initialized': False, 'test_passed': False, 'error': '未初始化'}
        
        # 2. 检查 Bloomberg
        if self._bloomberg_available:
            try:
                price = self._get_price_from_bloomberg(test_code)
                results['Bloomberg'] = {
                    'initialized': True,
                    'test_passed': price is not None and price > 0,
                    'error': None if price is not None and price > 0 else '无法获取测试数据'
                }
            except Exception as e:
                results['Bloomberg'] = {
                    'initialized': True,
                    'test_passed': False,
                    'error': str(e)
                }
        else:
            results['Bloomberg'] = {'initialized': False, 'test_passed': False, 'error': '未初始化'}
        
        # 3. 检查 Workspace
        if self._workspace_available:
            try:
                price = self._get_price_from_workspace(test_code)
                results['Refinitiv Workspace'] = {
                    'initialized': True,
                    'test_passed': price is not None and price > 0,
                    'error': None if price is not None and price > 0 else '无法获取测试数据'
                }
            except Exception as e:
                results['Refinitiv Workspace'] = {
                    'initialized': True,
                    'test_passed': False,
                    'error': str(e)
                }
        else:
            results['Refinitiv Workspace'] = {'initialized': False, 'test_passed': False, 'error': '未初始化'}
        
        # 4. 检查 AkShare
        if self._akshare_available:
            try:
                price = self._get_price_from_akshare(test_code)
                results['AkShare'] = {
                    'initialized': True,
                    'test_passed': price is not None and price > 0,
                    'error': None if price is not None and price > 0 else '无法获取测试数据'
                }
            except Exception as e:
                results['AkShare'] = {
                    'initialized': True,
                    'test_passed': False,
                    'error': str(e)
                }
        else:
            results['AkShare'] = {'initialized': False, 'test_passed': False, 'error': '未初始化'}
        
        return results
    
    def close(self) -> None:
        """关闭所有数据源连接"""
        if self._wind_available and self._wind_conn is not None:
            try:
                self._wind_conn.close()
                logger.info("Wind API 连接已关闭")
            except Exception as e:
                logger.warning(f"关闭 Wind API 连接失败: {e}")
        
        if self._workspace_available:
            try:
                import refinitiv.data as rd
                rd.close_session()
                logger.info("Refinitiv Workspace API 连接已关闭")
            except Exception as e:
                logger.warning(f"关闭 Workspace API 连接失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def get_price_with_fallback(
        self, 
        code: str, 
        user_prompt_callback=None,
        preferred_source: str = None
    ) -> Optional[float]:
        """
        获取价格，支持多数据源自动切换和用户提示
        
        优先级: Wind -> Bloomberg -> Workspace -> 手动输入
        
        Args:
            code: 股票代码
            user_prompt_callback: 用户提示回调函数，接收(数据源名称, 错误信息)参数
                                返回 True 表示用户已启动软件，继续尝试
                                返回 False 表示跳过此数据源
            preferred_source: 优先使用的数据源名称（'Wind', 'Bloomberg', 'Refinitiv Workspace'）
                            如果指定，会优先尝试该数据源
        
        Returns:
            最新价格，所有数据源都失败时返回 None
        """
        code = self._normalize_code(code)
        sources = [
            ('Wind', self._wind_available, self._get_price_from_wind),
            ('Bloomberg', self._bloomberg_available, self._get_price_from_bloomberg),
            ('Refinitiv Workspace', self._workspace_available, self._get_price_from_workspace),
        ]
        
        # 如果指定了优先数据源，将其移到列表最前面
        if preferred_source:
            sources = sorted(sources, key=lambda x: 0 if x[0] == preferred_source else 1)
        
        for source_name, is_available, fetch_func in sources:
            # 如果数据源不可用
            if not is_available:
                # 如果指定了优先数据源，且当前就是优先数据源，但不可用
                # 说明用户已经在 main.py 中选择跳过，这里直接尝试下一个
                if preferred_source and source_name == preferred_source:
                    logger.debug(f"优先数据源 {source_name} 不可用，尝试下一个")
                    continue
                
                # 提示用户启动（只有在没有指定优先数据源时才提示）
                if user_prompt_callback and not preferred_source:
                    print(f"\n⚠️ {source_name} 未连接")
                    print(f"   请启动 {source_name} 终端软件")
                    
                    retry = user_prompt_callback(source_name, f"{source_name} 未启动")
                    if retry:
                        # 用户表示已启动，重新初始化
                        if source_name == 'Wind':
                            self._init_wind()
                            is_available = self._wind_available
                        elif source_name == 'Bloomberg':
                            self._init_bloomberg()
                            is_available = self._bloomberg_available
                        elif source_name == 'Refinitiv Workspace':
                            self._init_workspace()
                            is_available = self._workspace_available
                    else:
                        # 用户选择跳过，继续下一个数据源
                        continue
                else:
                    # 没有回调函数或已指定优先数据源，直接跳过
                    continue
            
            # 现在尝试获取价格（数据源应该已可用）
            try:
                price = fetch_func(code)
                if price is not None and not pd.isna(price) and price > 0:
                    logger.info(f"从 {source_name} 获取 {code} 价格成功: {price}")
                    return price
            except Exception as e:
                logger.warning(f"{source_name} 获取 {code} 价格失败: {e}")
                
                # 如果有用户提示回调，询问用户是否启动软件
                if user_prompt_callback:
                    print(f"\n⚠️ {source_name} 获取价格失败")
                    print(f"   错误: {e}")
                    print(f"   请检查 {source_name} 是否已启动")
                    
                    retry = user_prompt_callback(source_name, str(e))
                    if retry:
                        # 用户表示已启动，重新初始化并尝试
                        if source_name == 'Wind':
                            self._init_wind()
                        elif source_name == 'Bloomberg':
                            self._init_bloomberg()
                        elif source_name == 'Refinitiv Workspace':
                            self._init_workspace()
                        
                        # 重新尝试
                        try:
                            price = fetch_func(code)
                            if price is not None and not pd.isna(price) and price > 0:
                                logger.info(f"从 {source_name} 获取 {code} 价格成功: {price}")
                                return price
                        except Exception as e2:
                            logger.warning(f"{source_name} 重试获取 {code} 价格失败: {e2}")
        
        # 所有数据源都失败
        logger.error(f"所有数据源都无法获取 {code} 的价格")
        return None
    
    def get_history_with_fallback(
        self, 
        code: str, 
        start_date: str, 
        end_date: str,
        user_prompt_callback=None
    ) -> Optional[pd.DataFrame]:
        """
        获取历史价格，支持多数据源自动切换和用户提示
        
        优先级: Wind -> Bloomberg -> Workspace -> 手动输入
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            user_prompt_callback: 用户提示回调函数
        
        Returns:
            DataFrame 包含历史价格，所有数据源都失败时返回 None
        """
        code = self._normalize_code(code)
        sources = [
            ('Wind', self._wind_available, self._get_history_from_wind),
            ('Bloomberg', self._bloomberg_available, self._get_history_from_bloomberg),
            ('Refinitiv Workspace', self._workspace_available, self._get_history_from_workspace),
        ]
        
        for source_name, is_available, fetch_func in sources:
            # 如果数据源不可用，提示用户启动
            if not is_available:
                if user_prompt_callback:
                    print(f"\n⚠️ {source_name} 未连接")
                    print(f"   请启动 {source_name} 终端软件")
                    
                    retry = user_prompt_callback(source_name, f"{source_name} 未启动")
                    if retry:
                        # 用户表示已启动，重新初始化
                        if source_name == 'Wind':
                            self._init_wind()
                            is_available = self._wind_available
                        elif source_name == 'Bloomberg':
                            self._init_bloomberg()
                            is_available = self._bloomberg_available
                        elif source_name == 'Refinitiv Workspace':
                            self._init_workspace()
                            is_available = self._workspace_available
                    else:
                        # 用户选择跳过，继续下一个数据源
                        continue
                else:
                    # 没有回调函数，直接跳过
                    continue
            
            # 现在尝试获取历史价格（数据源应该已可用）
            try:
                prices = fetch_func(code, start_date, end_date)
                if prices is not None and not prices.empty:
                    logger.info(f"从 {source_name} 获取 {code} 历史价格成功，共 {len(prices)} 条")
                    return prices
            except Exception as e:
                logger.warning(f"{source_name} 获取 {code} 历史价格失败: {e}")
                
                # 如果有用户提示回调，询问用户是否启动软件
                if user_prompt_callback:
                    print(f"\n⚠️ {source_name} 获取历史价格失败")
                    print(f"   错误: {e}")
                    print(f"   请检查 {source_name} 是否已启动")
                    
                    retry = user_prompt_callback(source_name, str(e))
                    if retry:
                        # 用户表示已启动，重新初始化并尝试
                        if source_name == 'Wind':
                            self._init_wind()
                        elif source_name == 'Bloomberg':
                            self._init_bloomberg()
                        elif source_name == 'Refinitiv Workspace':
                            self._init_workspace()
                        
                        # 重新尝试
                        try:
                            prices = fetch_func(code, start_date, end_date)
                            if prices is not None and not prices.empty:
                                logger.info(f"从 {source_name} 获取 {code} 历史价格成功，共 {len(prices)} 条")
                                return prices
                        except Exception as e2:
                            logger.warning(f"{source_name} 重试获取 {code} 历史价格失败: {e2}")
        
        # 所有数据源都失败
        logger.error(f"所有数据源都无法获取 {code} 的历史价格")
        return None
