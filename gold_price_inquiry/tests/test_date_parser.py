"""
黄金价格查询工具测试
"""

import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gold_price_inquiry import NaturalLanguageDateParser


class TestNaturalLanguageDateParser:
    """自然语言时间解析器测试"""

    def setup_method(self):
        self.parser = NaturalLanguageDateParser()

    def test_parse_quarter_1(self):
        """测试1季度解析"""
        start, end, desc = self.parser.parse("2026年1季度")
        assert start.month == 1
        assert end.month == 3
        assert "2026年1季度" in desc

    def test_parse_quarter_q1(self):
        """测试Q1解析"""
        start, end, desc = self.parser.parse("Q1")
        assert start.month == 1
        assert end.month == 3

    def test_parse_chinese_new_year(self):
        """测试春节解析"""
        start, end, desc = self.parser.parse("2023年春节")
        assert start.year == 2023
        assert "春节" in desc

    def test_parse_national_day(self):
        """测试国庆节解析"""
        start, end, desc = self.parser.parse("国庆节")
        assert start.month == 10
        assert end.month == 10
        assert "国庆节" in desc

    def test_parse_this_year(self):
        """测试今年解析"""
        current_year = datetime.now().year
        start, end, desc = self.parser.parse("今年")
        assert start.year == current_year
        assert end.year == current_year

    def test_parse_last_year(self):
        """测试去年解析"""
        current_year = datetime.now().year
        start, end, desc = self.parser.parse("去年")
        assert start.year == current_year - 1

    def test_parse_month_early(self):
        """测试月上旬解析"""
        start, end, desc = self.parser.parse("3月上旬")
        assert start.month == 3
        assert start.day == 1
        assert end.day == 10

    def test_parse_month_mid(self):
        """测试月中旬解析"""
        start, end, desc = self.parser.parse("5月中旬")
        assert start.month == 5
        assert start.day == 11
        assert end.day == 20

    def test_parse_month_late(self):
        """测试月下旬解析"""
        start, end, desc = self.parser.parse("7月下旬")
        assert start.month == 7
        assert start.day == 21


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
