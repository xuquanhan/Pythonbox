#!/usr/bin/env python3
"""
微信公众号自动登录模块（简化版）
不使用selenium-wire，使用普通selenium + 手动输入参数
"""

import time
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
import logging

logger = logging.getLogger(__name__)

class WeChatAutoLoginSimple:
    """微信公众号自动登录类（简化版）"""
    
    def __init__(self, session_file='config/wechat_session.json'):
        self.session_file = session_file
        self.driver = None
        self.session_data = self._load_session()
        
    def _load_session(self):
        """加载已保存的会话信息"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载会话文件失败: {e}")
        return {}
    
    def _save_session(self, data):
        """保存会话信息"""
        try:
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("会话信息已保存")
        except Exception as e:
            logger.error(f"保存会话文件失败: {e}")
    
    def _init_driver(self):
        """初始化浏览器"""
        edge_options = EdgeOptions()
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-gpu')
        
        # 尝试使用系统msedgedriver
        try:
            custom_driver_path = r"C:\msedgedriver\msedgedriver.exe"
            if os.path.exists(custom_driver_path):
                edge_service = EdgeService(executable_path=custom_driver_path)
                self.driver = webdriver.Edge(service=edge_service, options=edge_options)
                logger.info(f"使用自定义路径msedgedriver: {custom_driver_path}")
            else:
                self.driver = webdriver.Edge(options=edge_options)
                logger.info("使用系统默认msedgedriver")
        except Exception as e:
            logger.error(f"初始化浏览器失败: {e}")
            return False
        
        return True
    
    def is_session_valid(self):
        """检查会话是否有效"""
        if not self.session_data:
            return False
        
        # 检查是否有必要的字段
        if 'token' not in self.session_data or 'cookie' not in self.session_data:
            return False
        
        # 检查是否过期（假设2天过期）
        if 'login_time' in self.session_data:
            login_time = datetime.fromisoformat(self.session_data['login_time'])
            if datetime.now() - login_time > timedelta(days=2):
                logger.info("会话已过期，需要重新登录")
                return False
        
        return True
    
    def login(self):
        """
        执行自动登录流程
        返回：是否登录成功
        """
        if self.is_session_valid():
            logger.info("使用已保存的会话信息")
            print("\n[✓] 检测到已保存的登录信息，无需重新扫码")
            return True
        
        logger.info("开始自动登录流程...")
        
        if not self._init_driver():
            return False
        
        try:
            # 1. 访问登录页面
            logger.info("打开微信公众号登录页面...")
            self.driver.get("https://mp.weixin.qq.com/")
            
            # 2. 等待二维码出现
            logger.info("等待二维码加载...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "login__type__container__scan__qrcode"))
                )
                logger.info("二维码已显示，请使用微信扫码登录")
                print("\n" + "="*60)
                print("请使用微信扫描页面上的二维码登录")
                print("="*60 + "\n")
            except Exception as e:
                logger.warning(f"等待二维码超时: {e}")
            
            # 3. 等待登录成功（检测URL中是否出现token）
            logger.info("等待扫码登录...")
            max_wait = 120  # 最多等待2分钟
            start_time = time.time()
            token = None
            
            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url
                if "token" in current_url:
                    # 提取token
                    parsed_url = urlparse(current_url)
                    token = parse_qs(parsed_url.query).get("token", [""])[0]
                    logger.info(f"登录成功，获取到token: {token}")
                    break
                time.sleep(1)
            
            if not token:
                logger.error("登录超时，未获取到token")
                return False
            
            # 4. 获取cookie
            logger.info("获取cookie...")
            cookies = self.driver.get_cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # 5. 保存会话信息
            self.session_data = {
                'token': token,
                'cookie': cookie_str,
                'login_time': datetime.now().isoformat(),
                'cookies_list': cookies
            }
            self._save_session(self.session_data)
            
            logger.info("自动登录完成，会话信息已保存")
            print("\n[✓] 登录成功！会话信息已保存")
            return True
            
        except Exception as e:
            logger.error(f"自动登录失败: {e}")
            return False
    
    def get_fakeid_interactive(self, account_name):
        """
        交互式获取公众号fakeid
        由于不使用selenium-wire，需要用户手动从浏览器开发者工具中复制
        """
        if not self.driver:
            logger.error("浏览器未初始化")
            return None
        
        try:
            # 1. 跳转到超链接页面
            token = self.session_data.get('token')
            timestamp = int(time.time() * 1000)
            new_url = (
                f"https://mp.weixin.qq.com/cgi-bin/appmsg?"
                f"t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0"
                f"&token={token}&lang=zh_CN&timestamp={timestamp}"
            )
            
            logger.info(f"跳转到超链接页面...")
            self.driver.get(new_url)
            time.sleep(3)
            
            # 2. 点击"插入链接"按钮
            logger.info("点击插入链接按钮...")
            try:
                insert_link_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "js_editor_insertlink"))
                )
                insert_link_btn.click()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"点击插入链接按钮失败: {e}")
            
            # 3. 点击"选择其他公众号"
            logger.info("点击选择其他公众号...")
            try:
                select_other_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".weui-desktop-btn.weui-desktop-btn_default"))
                )
                select_other_btn.click()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"点击选择其他公众号失败: {e}")
            
            # 4. 输入公众号名称搜索
            logger.info(f"搜索公众号: {account_name}")
            try:
                input_box = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((
                        By.XPATH,
                        "//input[@class='weui-desktop-form__input' and @placeholder='输入文章来源的账号名称或微信号，回车进行搜索']"
                    ))
                )
                input_box.clear()
                input_box.send_keys(account_name)
                time.sleep(1)
                
                # 点击搜索按钮
                search_btn = self.driver.find_element(By.CSS_SELECTOR, ".weui-desktop-icon.weui-desktop-icon__search")
                search_btn.click()
                time.sleep(3)
            except Exception as e:
                logger.error(f"输入搜索关键词失败: {e}")
                return None
            
            # 5. 提示用户手动获取fakeid
            print(f"\n{'='*60}")
            print(f"请手动获取 {account_name} 的fakeid")
            print(f"{'='*60}")
            print("操作步骤：")
            print("1. 在浏览器中按 F12 打开开发者工具")
            print("2. 切换到 Network (网络) 标签")
            print("3. 点击搜索结果的公众号")
            print("4. 在请求列表中找到包含 'fakeid' 的请求")
            print("5. 复制 fakeid 的值")
            print("="*60)
            
            fakeid = input(f"\n请输入 {account_name} 的 fakeid: ").strip()
            
            if fakeid:
                logger.info(f"获取到fakeid: {fakeid}")
                return fakeid
            else:
                logger.warning("未输入fakeid")
                return None
            
        except Exception as e:
            logger.error(f"搜索公众号失败: {e}")
            return None
    
    def get_fakeid_by_api(self, account_name):
        """
        使用API直接获取公众号fakeid（全自动）
        通过调用微信公众号后台的searchbiz接口
        """
        import requests
        
        if not self.session_data.get('token') or not self.session_data.get('cookie'):
            logger.error("未获取到token或cookie，无法调用API")
            return None
        
        try:
            logger.info(f"使用API搜索公众号: {account_name}")
            
            # 构建请求参数
            token = self.session_data.get('token')
            cookie = self.session_data.get('cookie')
            
            url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token={token}&lang=zh_CN",
                "Cookie": cookie,
                "X-Requested-With": "XMLHttpRequest"
            }
            
            params = {
                "token": token,
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1",
                "action": "search_biz",
                "begin": "0",
                "count": "5",
                "query": account_name,
                "type": "1"  # 搜索公众号
            }
            
            logger.info(f"发送搜索请求: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code}")
                return None
            
            data = response.json()
            
            # 检查是否登录过期
            if data.get('base_resp', {}).get('ret') == 200003:
                logger.error("登录已过期，需要重新登录")
                return None
            
            # 检查是否有错误
            if data.get('base_resp', {}).get('ret') != 0:
                logger.error(f"API返回错误: {data.get('base_resp', {})}")
                return None
            
            # 解析搜索结果
            biz_list = data.get('list', [])
            
            if not biz_list:
                logger.warning(f"未找到公众号: {account_name}")
                return None
            
            # 找到匹配的公众号
            for biz in biz_list:
                nickname = biz.get('nickname', '')
                fakeid = biz.get('fakeid', '')
                
                if nickname == account_name or account_name in nickname:
                    logger.info(f"找到公众号: {nickname}, fakeid: {fakeid}")
                    return fakeid
            
            # 如果没有精确匹配，返回第一个结果
            first_biz = biz_list[0]
            fakeid = first_biz.get('fakeid', '')
            nickname = first_biz.get('nickname', '')
            logger.info(f"使用最佳匹配: {nickname}, fakeid: {fakeid}")
            return fakeid
            
        except Exception as e:
            logger.error(f"API搜索公众号失败: {e}")
            return None
    
    def get_session(self):
        """获取当前会话信息"""
        return self.session_data
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器失败: {e}")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    auto_login = WeChatAutoLoginSimple()
    
    # 尝试登录
    if auto_login.login():
        print("登录成功！")
        print(f"Token: {auto_login.session_data.get('token')}")
        
        # 测试获取fakeid
        fakeid = auto_login.get_fakeid_interactive("人民日报")
        if fakeid:
            print(f"获取到fakeid: {fakeid}")
    else:
        print("登录失败")
    
    auto_login.close()
