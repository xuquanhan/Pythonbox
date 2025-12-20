#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import os
import re
import sys

# 设置标准输出编码为UTF-8，解决Windows命令行中文乱码问题
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- 配置 ---
API_KEY = "2360a68c16b805cf2a02db06372ce22c"
BASE_URL = "https://fedinprint.org/api"
ITEMS_PER_PAGE = 100


def ask_search_scope() -> int:
    while True:
        choice = input(
            "请输入搜索范围：\n"
            "0 - 标题 + 摘要\n"
            "1 - 标题\n"
            "2 - 摘要\n"
            "请输入 0 / 1 / 2："
        ).strip()
        if choice in {"0", "1", "2"}:
            return int(choice)
        print("输入无效，请重新输入：")


def extract_year_from_title(title: str) -> str:
    m = re.search(r'\b(19|20)\d{2}\b', title)
    return m.group() if m else "N/A"


def build_endpoint_and_params(scope: int, keyword: str):
    if not keyword:
        return f"{BASE_URL}/item", {}
    if scope == 0:
        return f"{BASE_URL}/item/search", {"title": keyword, "abstract": keyword}
    elif scope == 1:
        return f"{BASE_URL}/item/search", {"title": keyword}
    else:  # scope == 2
        return f"{BASE_URL}/item/search", {"abstract": keyword}


def get_articles(keyword: str, scope: int):
    endpoint, params = build_endpoint_and_params(scope, keyword)
    if keyword:
        scope_desc = ["标题+摘要", "标题", "摘要"][scope]
        print(f"正在搜索 {scope_desc} 中包含'{keyword}' 的文章..")
    else:
        print("正在获取所有文章..")

    session = requests.Session()
    session.headers.update({"X-API-Key": API_KEY})

    all_articles = []
    page = 1
    while True:
        params['limit'] = ITEMS_PER_PAGE
        params['page'] = page

        try:
            data = session.get(endpoint, params=params, timeout=30).json()
            records = data.get("records", [])
            if not records:
                print("没有更多结果，获取完毕。")
                break

            for rec in records:
                if not isinstance(rec, dict):
                    continue

                authors_data = rec.get("author", [])
                if isinstance(authors_data, list):
                    authors = ", ".join(
                        a.get("name", "Unknown") if isinstance(a, dict) else str(a)
                        for a in authors_data
                    )
                else:
                    authors = str(authors_data) if authors_data else "N/A"

                file_url = ""
                if isinstance(rec.get("file"), list) and rec["file"]:
                    file_url = (
                        rec["file"][0].get("fileurl", "")
                        if isinstance(rec["file"][0], dict)
                        else ""
                    )

                pub_date = rec.get("publication_date") or rec.get("publicationDate")
                year = pub_date if pub_date else extract_year_from_title(rec.get("title", ""))

                article_data = {
                    "title": rec.get("title", "N/A"),
                    "authors": authors,
                    "year": year,
                    "pages": rec.get("pages", "N/A"),
                    "url": file_url,
                    "id": rec.get("id", "N/A"),
                    "abstract": rec.get("abstract", "N/A"),
                }

                # 过滤逻辑
                if keyword:
                    title_lower = article_data["title"].lower()
                    abstract_lower = article_data["abstract"].lower()
                    kw_lower = keyword.lower()

                    if scope == 0 and (kw_lower in title_lower or kw_lower in abstract_lower):
                        all_articles.append(article_data)
                    elif scope == 1 and kw_lower in title_lower:
                        all_articles.append(article_data)
                    elif scope == 2 and kw_lower in abstract_lower:
                        all_articles.append(article_data)
                else:
                    all_articles.append(article_data)

            page += 1
        except Exception as e:
            print("请求出错:", e)
            break
    return all_articles


def save_to_csv(articles, filename):
    if not articles:
        print("没有找到任何文章，无需创建文件。")
        return
    try:
        # 现在把 abstract 正式加进 CSV
        fieldnames = ["title", "authors", "year", "pages", "url", "id", "abstract"]
        # 使用 utf-8-sig 编码解决 Excel 打开中文乱码问题
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)
        print(f"\n成功! {len(articles)} 条记录已保存到 {os.path.abspath(filename)}")
    except IOError as e:
        print("写入文件时发生 I/O 错误:", e)


def display_articles(articles):
    if not articles:
        print("没有获取到文章。")
        return
    print(f"\n获取到 {len(articles)} 篇文章")
    print("-" * 80)
    for i, art in enumerate(articles, 1):
        print(f"{i}. 标题  : {art['title']}")
        print(f"   作者  : {art['authors']}")
        print(f"   年份  : {art['year']}")
        print(f"   页码  : {art['pages']}")
        print(f"   ID    : {art['id']}")
        print(f"   摘要  : {art['abstract'][:300]}{'...' if len(art['abstract']) > 300 else ''}")
        print()


if __name__ == "__main__":
    keyword = input("请输入搜索关键词 (按 Enter 获取所有文章): ").strip()
    scope = ask_search_scope()
    articles = get_articles(keyword, scope)
    display_articles(articles)
    if articles:
        safe = keyword.replace(' ', '_').replace('/', '_') if keyword else "all"
        save_to_csv(articles, f"fed_articles_{safe}.csv")
