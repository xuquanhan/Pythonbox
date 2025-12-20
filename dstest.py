# 导入各种库
import os
import re
import json
import math
import numpy as np
import pandas as pd
import tushare as ts
import xlsxwriter
import requests
from bs4 import BeautifulSoup
import time
import random
from WindPy import w
import matplotlib.pyplot as plt
import datetime
from datetime import timedelta


def ai_summarize_news(news_text):
    """
    使用AI对新闻进行简短分析（30字左右），注意修改降息、加息周期
    """
    # deepseek所使用的API
    API_KEY = "sk-686ccc9e91b54750b8e4d1d3184717a2"
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        data = {
            "model": "deepseek-reasoner",  # 指定使用 R1 模型（deepseek-reasoner）或者 V3 模型（deepseek-chat）
            "messages": [
                {"role": "system", "content": "你是一个专业的财经分析师，请用30字左右对新闻进行简短分析。"},
                {"role": "user", "content": f"今天是{datetime.date.today()}，美联储正处在降息周期。你是一个专业的财经分析师，\
                在注意时效性的情况下，请用30字左右对新闻进行简短分析：{news_text}"}
            ],
            "max_tokens": 1000
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    except Exception as e:
        print(f"AI分析时发生错误：{e}")
        return "【AI分析】分析生成失败"


if __name__ == "__main__":
    ai_answer = ai_summarize_news("巴基斯坦与阿富汗在边境地区交火，巴基斯坦关闭与阿富汗边境口岸。")
    print("")