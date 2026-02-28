# -*- coding: utf-8 -*-
"""
黄金价格查询工具

功能：
- 支持自然语言输入查询时间段（如"2026年1季度"、"2023年中国春节假期期间"）
- 通过Bloomberg API获取伦敦现货黄金（XAU USD）数据
- 获取SPDR黄金ETF（GLD US）持仓变化
- 展示区间开盘价、最高价、最低价、涨跌幅等信息
- 支持AkShare作为备选数据源
"""

from datetime import datetime, timedelta
import re
import tkinter as tk
from tkinter import simpledialog, messagebox
import sys


try:
    import blpapi
    BLOOMBERG_AVAILABLE = True
except ImportError:
    BLOOMBERG_AVAILABLE = False

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class NaturalLanguageDateParser:
    """自然语言时间解析器"""

    def __init__(self):
        self.current_year = datetime.now().year

        self.chinese_holidays = {
            "春节": {"description": "中国农历新年"},
            "元旦": {"description": "1月1日"},
            "清明节": {"description": "4月4日-4月6日"},
            "劳动节": {"description": "5月1日-5月3日"},
            "端午节": {"description": "农历五月初五"},
            "中秋节": {"description": "农历八月十五"},
            "国庆节": {"description": "10月1日-10月7日"}
        }

    def parse(self, text: str) -> tuple:
        text = text.strip()
        year = self._extract_year(text)

        if "季度" in text or any(q in text.upper() for q in ["Q1", "Q2", "Q3", "Q4"]):
            return self._parse_quarter(text, year)
        elif "月" in text and ("初" in text or "中" in text or "末" in text or "上旬" in text or "中旬" in text or "下旬" in text):
            return self._parse_month_period(text, year)
        elif "年" in text and "至" in text:
            return self._parse_date_range(text, year)
        elif any(holiday in text for holiday in self.chinese_holidays.keys()):
            return self._parse_holiday(text, year)
        elif "上半年" in text:
            return self._parse_half_year(text, year, "first")
        elif "下半年" in text:
            return self._parse_half_year(text, year, "second")
        elif "今年" in text:
            return self._parse_current_year(text)
        elif "去年" in text:
            return self._parse_last_year(text)
        elif "明年" in text:
            return self._parse_next_year(text)
        else:
            return self._parse_direct_date(text, year)

    def _extract_year(self, text: str) -> int:
        year_pattern = r'(\d{4})年?'
        match = re.search(year_pattern, text)
        if match:
            return int(match.group(1))

        if "今年" in text or "本年度" in text:
            return self.current_year
        elif "去年" in text or "上一年" in text:
            return self.current_year - 1
        elif "明年" in text or "下一年" in text:
            return self.current_year + 1

        return self.current_year

    def _parse_quarter(self, text: str, year: int) -> tuple:
        quarter_map = {
            "1季度": (1, 1, 3, 31), "一季度": (1, 1, 3, 31), "Q1": (1, 1, 3, 31),
            "2季度": (4, 4, 6, 30), "二季度": (4, 4, 6, 30), "Q2": (4, 4, 6, 30),
            "3季度": (7, 7, 9, 30), "三季度": (7, 7, 9, 30), "Q3": (7, 7, 9, 30),
            "4季度": (10, 10, 12, 31), "四季度": (10, 10, 12, 31), "Q4": (10, 10, 12, 31),
        }

        for q_key, (start_month, start_day, end_month, end_day) in quarter_map.items():
            if q_key in text:
                start_date = datetime(year, start_month, start_day)
                end_date = datetime(year, end_month, end_day)
                return (start_date, end_date, f"{year}年{q_key}")

        return (datetime.now(), datetime.now()), ""

    def _parse_month_period(self, text: str, year: int) -> tuple:
        month_pattern = r'(\d{1,2})月'
        match = re.search(month_pattern, text)
        if not match:
            return (datetime.now(), datetime.now()), ""

        month = int(match.group(1))
        if month < 1 or month > 12:
            return (datetime.now(), datetime.now()), ""

        if "上旬" in text or "初" in text:
            start_day, end_day = 1, 10
            period_name = "上旬"
        elif "中旬" in text:
            start_day, end_day = 11, 20
            period_name = "中旬"
        elif "下旬" in text or "末" in text:
            start_day, end_day = 21, self._get_month_days(year, month)
            period_name = "下旬"
        else:
            return (datetime(year, month, 1), datetime(year, month, self._get_month_days(year, month)), f"{year}年{month}月")

        start_date = datetime(year, month, start_day)
        end_date = datetime(year, month, end_day)
        return (start_date, end_date, f"{year}年{month}月{period_name}")

    def _get_month_days(self, year: int, month: int) -> int:
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            return 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
        return 30

    def _parse_date_range(self, text: str, year: int) -> tuple:
        range_pattern = r'(\d{1,2})月(\d{1,2})日?\s*至\s*(\d{1,2})月(\d{1,2})日?'
        match = re.search(range_pattern, text)
        if match:
            start_month, start_day = int(match.group(1)), int(match.group(2))
            end_month, end_day = int(match.group(3)), int(match.group(4))
            start_date = datetime(year, start_month, start_day)
            end_date = datetime(year, end_month, end_day)
            return (start_date, end_date, f"{year}年{start_month}月{start_day}日至{end_month}月{end_day}日")
        return (datetime.now(), datetime.now()), ""

    def _parse_holiday(self, text: str, year: int) -> tuple:
        holiday_dates = self._get_holiday_dates(year)
        for holiday_name, (start_date, end_date) in holiday_dates.items():
            if holiday_name in text:
                return (start_date, end_date, f"{year}年{holiday_name}")
        return (datetime.now(), datetime.now()), ""

    def _get_holiday_dates(self, year: int) -> dict:
        holidays = {
            "元旦": (datetime(year, 1, 1), datetime(year, 1, 1)),
            "春节": self._get_lunar_new_year_range(year),
            "清明节": (datetime(year, 4, 4), datetime(year, 4, 6)),
            "劳动节": (datetime(year, 5, 1), datetime(year, 5, 3)),
            "端午节": self._get_dragon_boat_festival(year),
            "中秋节": self._get_mid_autumn_festival(year),
            "国庆节": (datetime(year, 10, 1), datetime(year, 10, 7)),
        }
        return holidays

    def _get_lunar_new_year_range(self, year: int) -> tuple:
        lunar_new_year_dates = {2023: (1, 22), 2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2027: (2, 6)}
        if year in lunar_new_year_dates:
            month, day = lunar_new_year_dates[year]
            start_date = datetime(year, month, day)
            return (start_date, start_date + timedelta(days=6))
        fallback_date = datetime(year, 2, 1)
        return (fallback_date, fallback_date + timedelta(days=6))

    def _get_dragon_boat_festival(self, year: int) -> tuple:
        dates = {2023: (6, 22), 2024: (6, 10), 2025: (5, 29), 2026: (6, 17)}
        if year in dates:
            month, day = dates[year]
            return (datetime(year, month, day), datetime(year, month, day + 2))
        return (datetime(year, 6, 1), datetime(year, 6, 3))

    def _get_mid_autumn_festival(self, year: int) -> tuple:
        dates = {2023: (9, 29), 2024: (9, 17), 2025: (10, 6), 2026: (9, 25)}
        if year in dates:
            month, day = dates[year]
            days_in_month = self._get_month_days(year, month)
            end_day = day + 1 if day + 1 <= days_in_month else days_in_month
            return (datetime(year, month, day), datetime(year, month, end_day))
        return (datetime(year, 9, 15), datetime(year, 9, 17))

    def _parse_half_year(self, text: str, year: int, half: str) -> tuple:
        if half == "first":
            return (datetime(year, 1, 1), datetime(year, 6, 30), f"{year}年上半年")
        return (datetime(year, 7, 1), datetime(year, 12, 31), f"{year}年下半年")

    def _parse_current_year(self, text: str) -> tuple:
        year = self.current_year
        return (datetime(year, 1, 1), datetime(year, 12, 31), f"{year}年全年")

    def _parse_last_year(self, text: str) -> tuple:
        year = self.current_year - 1
        return (datetime(year, 1, 1), datetime(year, 12, 31), f"{year}年全年")

    def _parse_next_year(self, text: str) -> tuple:
        year = self.current_year + 1
        return (datetime(year, 1, 1), datetime(year, 12, 31), f"{year}年全年")

    def _parse_direct_date(self, text: str, year: int) -> tuple:
        patterns = [
            (r'(\d{1,2})月(\d{1,2})日?', lambda m: (datetime(year, int(m.group(1)), int(m.group(2))),
                                                     datetime(year, int(m.group(1)), int(m.group(2))),
                                                     f"{year}年{m.group(1)}月{m.group(2)}日")),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: (datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))),
                                                         datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))),
                                                         f"{m.group(1)}年{m.group(2)}月{m.group(3)}日")),
        ]
        for pattern, handler in patterns:
            match = re.search(pattern, text)
            if match:
                return handler(match)
        return (datetime.now(), datetime.now()), ""


class BloombergGoldFetcher:
    """Bloomberg黄金数据获取器"""

    def __init__(self):
        self.session = None
        self.connected = False

    def connect(self) -> bool:
        if not BLOOMBERG_AVAILABLE:
            return False
        try:
            options = blpapi.SessionOptions()
            options.setServerHost("localhost")
            options.setServerPort(8194)
            self.session = blpapi.Session(options)
            if not self.session.start():
                return False
            if not self.session.openService("//blp/refdata"):
                return False
            self.connected = True
            return True
        except Exception as e:
            print(f"Bloomberg连接错误: {e}")
            return False

    def disconnect(self):
        if self.session:
            self.session.stop()
            self.connected = False

    def get_gold_price_data(self, start_date: datetime, end_date: datetime) -> dict:
        if not self.connected:
            return {"error": "未连接到Bloomberg"}

        try:
            service = self.session.getService("//blp/refdata")
            request = service.createRequest("HistoricalDataRequest")
            request.getElement("securities").appendValue("XAU USD Curncy")
            request.getElement("fields").appendValue("PX_OPEN")
            request.getElement("fields").appendValue("PX_HIGH")
            request.getElement("fields").appendValue("PX_LOW")
            request.getElement("fields").appendValue("PX_LAST")
            request.set("periodicityAdjustment", "CALENDAR")
            request.set("periodicitySelection", "DAILY")
            request.set("startDate", start_date.strftime("%Y%m%d"))
            request.set("endDate", end_date.strftime("%Y%m%d"))

            self.session.sendRequest(request)
            data_points = []

            while True:
                event = self.session.nextEvent()
                if event.eventType() == blpapi.Event.RESPONSE:
                    break
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        for i in range(security_data.numValues()):
                            field_data = security_data.getValue(i)
                            date = field_data.getElementAsString("date")
                            px_open = field_data.getElementAsFloat("PX_OPEN")
                            px_high = field_data.getElementAsFloat("PX_HIGH")
                            px_low = field_data.getElementAsFloat("PX_LOW")
                            px_last = field_data.getElementAsFloat("PX_LAST")
                            data_points.append({"date": date, "open": px_open, "high": px_high, "low": px_low, "close": px_last})

            if not data_points:
                return {"error": "未获取到黄金数据"}

            first_day = data_points[0]
            last_day = data_points[-1]
            prices = [d["close"] for d in data_points]
            price_change = last_day["close"] - first_day["open"]
            pct_change = (price_change / first_day["open"]) * 100

            return {
                "start_date": first_day["date"], "end_date": last_day["date"],
                "open": first_day["open"], "high": max(prices), "low": min(prices),
                "close": last_day["close"], "price_change": price_change, "pct_change": pct_change,
                "data_points": data_points
            }
        except Exception as e:
            return {"error": f"获取黄金数据时出错: {e}"}

    def get_spdr_gold_etf_change(self, start_date: datetime, end_date: datetime) -> dict:
        if not self.connected:
            return {"error": "未连接到Bloomberg"}

        try:
            service = self.session.getService("//blp/refdata")
            request = service.createRequest("HistoricalDataRequest")
            request.getElement("securities").appendValue("GLD US Equity")
            request.getElement("fields").appendValue("PX_LAST")
            request.set("periodicityAdjustment", "CALENDAR")
            request.set("periodicitySelection", "DAILY")
            request.set("startDate", start_date.strftime("%Y%m%d"))
            request.set("endDate", end_date.strftime("%Y%m%d"))

            self.session.sendRequest(request)
            data_points = []

            while True:
                event = self.session.nextEvent()
                if event.eventType() == blpapi.Event.RESPONSE:
                    break
                for msg in event:
                    if msg.hasElement("securityData"):
                        security_data = msg.getElement("securityData")
                        for i in range(security_data.numValues()):
                            field_data = security_data.getValue(i)
                            date = field_data.getElementAsString("date")
                            px_last = field_data.getElementAsFloat("PX_LAST")
                            data_points.append({"date": date, "close": px_last})

            if not data_points:
                return {"error": "未获取到SPDR黄金ETF数据"}

            first_day = data_points[0]
            last_day = data_points[-1]
            holdings_change = last_day["close"] - first_day["close"]

            return {
                "start_date": first_day["date"], "end_date": last_day["date"],
                "start_holdings": first_day["close"], "end_holdings": last_day["close"],
                "holdings_change": holdings_change, "data_points": data_points
            }
        except Exception as e:
            return {"error": f"获取SPDR黄金ETF数据时出错: {e}"}


class AkShareGoldFetcher:
    """AkShare黄金数据获取器（备选）"""

    def __init__(self):
        self.available = AKSHARE_AVAILABLE

    def get_gold_price_data(self, start_date: datetime, end_date: datetime) -> dict:
        if not self.available:
            return {"error": "AkShare未安装"}

        try:
            df = ak.spot_golden_benchmark_sge()

            if df is None or df.empty:
                return {"error": "未获取到黄金数据"}

            df.columns = ['date', 'evening_price', 'morning_price']
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            df = df.sort_values("date")

            if df.empty:
                return {"error": "所选时间段内无黄金数据"}

            df['close'] = df['evening_price']
            df['open'] = df['morning_price']
            df['high'] = df[['evening_price', 'morning_price']].max(axis=1)
            df['low'] = df[['evening_price', 'morning_price']].min(axis=1)

            first_day = df.iloc[0]
            last_day = df.iloc[-1]

            prices = df["close"].tolist()
            price_change = last_day["close"] - first_day["open"]
            pct_change = (price_change / first_day["open"]) * 100

            return {
                "start_date": str(first_day["date"])[:10], "end_date": str(last_day["date"])[:10],
                "open": first_day["open"], "high": df["high"].max(), "low": df["low"].min(),
                "close": last_day["close"], "price_change": price_change, "pct_change": pct_change,
                "data_points": df.to_dict("records")
            }
        except Exception as e:
            return {"error": f"获取黄金数据时出错: {e}"}

    def get_spdr_gold_etf_change(self, start_date: datetime, end_date: datetime) -> dict:
        if not self.available:
            return {"error": "AkShare未安装"}

        try:
            df = ak.fund_etf_hist_em(symbol="159934", period="daily", start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"))

            if df is None or df.empty:
                return {"error": "未获取到黄金ETF数据"}

            df = df.sort_values("日期")
            first_day = df.iloc[0]
            last_day = df.iloc[-1]

            return {
                "start_date": str(first_day["日期"])[:10], "end_date": str(last_day["日期"])[:10],
                "start_holdings": first_day["收盘"], "end_holdings": last_day["收盘"],
                "holdings_change": last_day["收盘"] - first_day["收盘"],
                "data_points": df.to_dict("records")
            }
        except Exception as e:
            return {"error": f"获取黄金ETF数据时出错: {e}"}


class GoldPriceInquiryApp:
    """黄金价格查询应用"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("黄金价格查询工具")
        self.root.geometry("650x450")

        self.date_parser = NaturalLanguageDateParser()
        self.bloomberg_fetcher = None
        self.akshare_fetcher = None
        self.data_source = None

        self.setup_ui()
        self.check_available_sources()

    def setup_ui(self):
        tk.Label(self.root, text="黄金价格查询工具", font=("Arial", 18, "bold")).pack(pady=15)

        tk.Label(self.root, text="请输入要查询的黄金时间段：\n（如：2026年1季度、2023年春节、国庆节、1月上旬等）",
                 font=("Arial", 11), justify=tk.CENTER).pack(pady=5)

        self.input_entry = tk.Entry(self.root, font=("Arial", 14), width=40)
        self.input_entry.pack(pady=10)

        tk.Button(self.root, text="查询", font=("Arial", 14), command=self.handle_query, width=15, height=1).pack(pady=10)

        self.result_text = tk.Text(self.root, font=("Arial", 11), width=65, height=12)
        self.result_text.pack(pady=10)

        self.status_label = tk.Label(self.root, text="", font=("Arial", 10), fg="blue")
        self.status_label.pack(pady=5)

    def check_available_sources(self):
        sources = []
        if BLOOMBERG_AVAILABLE:
            sources.append("Bloomberg")
        if AKSHARE_AVAILABLE:
            sources.append("AkShare")

        if not sources:
            self.update_status("警告: 未安装Bloomberg和AkShare，数据源不可用")
        else:
            self.update_status(f"可用数据源: {', '.join(sources)}")

    def handle_query(self):
        user_input = self.input_entry.get().strip()
        if not user_input:
            self.update_status("请输入查询时间段")
            return

        self.update_status("正在解析时间...")
        result = self.date_parser.parse(user_input)

        if len(result) == 2:
            start_date, end_date = result[0]
            description = result[1]
        else:
            start_date, end_date, description = result

        if not description:
            self.update_status("无法解析输入的时间，请重新输入")
            return

        self.update_status(f"解析结果: {description}\n时间段: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

        confirm = messagebox.askyesno("确认时间段",
            f"您输入的时间段解析为：\n{description}\n\n时间范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n\n是否确认查询？")

        if not confirm:
            self.update_status("请重新输入时间段")
            return

        self.query_data(start_date, end_date, description)

    def query_data(self, start_date: datetime, end_date: datetime, description: str):
        gold_data = {"error": "数据源不可用"}
        etf_data = {"error": "数据源不可用"}

        if BLOOMBERG_AVAILABLE:
            self.update_status("正在尝试连接Bloomberg...")
            self.bloomberg_fetcher = BloombergGoldFetcher()
            if self.bloomberg_fetcher.connect():
                self.data_source = "Bloomberg"
                self.update_status("正在通过Bloomberg获取黄金价格数据...")
                gold_data = self.bloomberg_fetcher.get_gold_price_data(start_date, end_date)
                self.update_status("正在通过Bloomberg获取SPDR黄金ETF数据...")
                etf_data = self.bloomberg_fetcher.get_spdr_gold_etf_change(start_date, end_date)
                self.bloomberg_fetcher.disconnect()
            else:
                self.update_status("Bloomberg连接失败，尝试使用AkShare...")

        if "error" in gold_data and AKSHARE_AVAILABLE:
            self.update_status("正在通过AkShare获取黄金价格数据...")
            self.akshare_fetcher = AkShareGoldFetcher()
            self.data_source = "AkShare"
            gold_data = self.akshare_fetcher.get_gold_price_data(start_date, end_date)
            etf_data = self.akshare_fetcher.get_spdr_gold_etf_change(start_date, end_date)

        if "error" in gold_data:
            gold_data = {"error": "无法获取数据，请安装Bloomberg或AkShare库"}

        if "error" in etf_data:
            etf_data = {"error": "无法获取SPDR黄金ETF数据"}

        self.display_results(gold_data, etf_data, description, start_date, end_date)

    def display_results(self, gold_data: dict, etf_data: dict, description: str, start_date: datetime, end_date: datetime):
        self.result_text.delete("1.0", tk.END)

        source_info = f"（数据源: {self.data_source}）" if self.data_source else ""

        output = f"========== {description} 黄金价格分析 {source_info}==========\n\n"
        output += f"查询时间段: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n\n"

        if "error" in gold_data:
            output += f"黄金数据获取失败: {gold_data['error']}\n"
        else:
            output += "【伦敦现货黄金 (XAU USD)】\n"
            output += f"  区间开盘价: ${gold_data['open']:.2f} 美元/盎司\n"
            output += f"  区间最高价: ${gold_data['high']:.2f} 美元/盎司\n"
            output += f"  区间最低价: ${gold_data['low']:.2f} 美元/盎司\n"
            output += f"  区间收盘价: ${gold_data['close']:.2f} 美元/盎司\n"
            output += f"  涨跌金额: {'+' if gold_data['price_change'] >= 0 else ''}{gold_data['price_change']:.2f} 美元/盎司\n"
            output += f"  涨跌幅: {'+' if gold_data['pct_change'] >= 0 else ''}{gold_data['pct_change']:.2f}%\n\n"

        if "error" in etf_data:
            output += f"SPDR黄金ETF数据获取失败: {etf_data['error']}\n"
        else:
            output += "【SPDR黄金ETF (GLD US) 持仓变化】\n"
            output += f"  期初持仓: {etf_data['start_holdings']:.2f} 吨\n"
            output += f"  期末持仓: {etf_data['end_holdings']:.2f} 吨\n"
            output += f"  持仓变化: {'+' if etf_data['holdings_change'] >= 0 else ''}{etf_data['holdings_change']:.2f} 吨\n"

        self.result_text.insert("1.0", output)
        self.update_status("查询完成")
        messagebox.showinfo("查询完成", "数据已获取完成，请查看结果")

    def update_status(self, message: str):
        self.status_label.config(text=message)
        self.root.update()

    def run(self):
        self.root.mainloop()


def main():
    print("=" * 50)
    print("黄金价格查询工具")
    print("=" * 50)
    print(f"Bloomberg API: {'可用' if BLOOMBERG_AVAILABLE else '不可用'}")
    print(f"AkShare: {'可用' if AKSHARE_AVAILABLE else '不可用'}")
    print("=" * 50)

    if not BLOOMBERG_AVAILABLE and not AKSHARE_AVAILABLE:
        print("\n警告: 两个数据源都不可用！")
        print("请至少安装其中一个:")
        print("  - Bloomberg: pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple blpapi")
        print("  - AkShare: pip install akshare")
        print("\n按回车键退出...")
        input()
        return

    app = GoldPriceInquiryApp()
    app.run()


if __name__ == "__main__":
    main()
