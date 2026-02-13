#!/usr/bin/env python3
"""
微信公众号自动登录模块
实现扫码登录、自动提取token和cookie
"""

import time
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
import logging

logger = logging.getLogger(__name__)

class WeChatAutoLogin:
    """微信公众号自动登录类"""
    
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
            return True
            
        except Exception as e:
            logger.error(f"自动登录失败: {e}")
            return False
    
    def search_account(self, account_name):
        """
        搜索公众号获取fakeid
        返回：fakeid或None
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
            
            # 5. 从请求中抓取fakeid
            logger.info("从网络请求中提取fakeid...")
            fakeid = None
            
            # 等待搜索请求完成
            time.sleep(3)
            
            for request in self.driver.requests:
                if "searchbiz" in request.url or "appmsg" in request.url:
                    logger.info(f"找到相关请求: {request.url}")
                    # 尝试从URL参数中提取fakeid
                    parsed = urlparse(request.url)
                    params = parse_qs(parsed.query)
                    if 'fakeid' in params:
                        fakeid = params['fakeid'][0]
                        logger.info(f"提取到fakeid: {fakeid}")
                        break
            
            if not fakeid:
                logger.warning("未能从请求中提取到fakeid")
            
            return fakeid
            
        except Exception as e:
            logger.error(f"搜索公众号失败: {e}")
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
    
    auto_login = WeChatAutoLogin()
    
    # 尝试登录
    if auto_login.login():
        print("登录成功！")
        print(f"Token: {auto_login.session_data.get('token')}")
        print(f"Cookie: {auto_login.session_data.get('cookie')[:100]}...")
        
        # 测试搜索公众号
        fakeid = auto_login.search_account("人民日报")
        if fakeid:
            print(f"获取到fakeid: {fakeid}")
        else:
            print("未能获取fakeid")
    else:
        print("登录失败")
    
    auto_login.close()
