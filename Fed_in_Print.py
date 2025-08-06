import requests
import csv
import os

# --- 配置 ---
API_KEY = "2360a68c16b805cf2a02db06372ce22c"
BASE_URL = "https://fedinprint.org/api"  # 注意：没有尾随空格
ITEMS_PER_PAGE = 100


def get_articles(keyword=None):
    if keyword:
        print(f"正在搜索标题中包含 '{keyword}' 的文章...")
        endpoint = f"{BASE_URL}/item/search"
        params = {"title": keyword}
    else:
        print("准备获取所有文章...")
        endpoint = f"{BASE_URL}/item"
        params = {}
    session = requests.Session()
    session.headers.update({"X-API-Key": API_KEY})

    all_articles = []
    page = 1

    while True:
        params['limit'] = ITEMS_PER_PAGE
        params['page'] = page

        try:
            print(f"正在获取第 {page} 页...")
            response = session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"API响应内容: {data}")  # 添加调试信息
            records = data.get("records", [])

            if not records:
                print("未找到更多记录，获取结束。")
                break

            for record in records:
                # 检查record是否为字典，如果不是则跳过
                if not isinstance(record, dict):
                    print(f"警告: 跳过无效记录类型 {type(record)}")
                    continue

                # 安全处理作者信息
                authors = "N/A"
                try:
                    authors_data = record.get("author", [])
                    if isinstance(authors_data, list):
                        author_names = []
                        for author in authors_data:
                            if isinstance(author, dict):
                                author_names.append(author.get("name", "Unknown"))
                            else:
                                author_names.append(str(author))
                        authors = ", ".join(author_names)
                    else:
                        authors = str(authors_data) if authors_data else "N/A"
                except Exception as e:
                    record_id = "未知"
                    if isinstance(record, dict):
                        record_id = record.get('id', 'N/A')
                    print(f"处理作者信息时出错 (ID: {record_id}): {e}")
                    authors = "N/A"

                file_url = ""
                if isinstance(record.get("file"), list) and len(record["file"]) > 0:
                    file_url = record["file"][0].get("fileurl", "") if isinstance(record["file"][0], dict) else ""

                article_data = {
                    "title": record.get("title", "N/A") if isinstance(record, dict) else "N/A",
                    "authors": authors,
                    "publication_date": record.get("publication_date",
                                                   record.get("publicationDate", "N/A")) if isinstance(record,
                                                                                                       dict) else "N/A",
                    "abstract": record.get("abstract", "N/A") if isinstance(record, dict) else "N/A",
                    "url": file_url,
                    "id": record.get("id", "N/A") if isinstance(record, dict) else "N/A"
                }
                
                # 如果指定了关键词，则只添加标题中包含关键词的文章
                if keyword:
                    title = article_data.get("title", "").lower()
                    if title and keyword.lower() in title:
                        all_articles.append(article_data)
                else:
                    all_articles.append(article_data)
                    
            page += 1
        except requests.exceptions.HTTPError as e:
            print(f"HTTP 错误: {e}")
            print(f"服务器可能拒绝了请求或出现了问题。服务器返回内容: {response.text}")
            break
        except requests.exceptions.RequestException as e:
            print(f"请求发生网络错误: {e}")
            break
        except ValueError:
            print(f"无法解析服务器返回的 JSON 数据。")
            print(f"服务器返回内容: {response.text}")
            break

    return all_articles


def save_to_csv(articles, filename):
    if not articles:
        print("没有找到任何文章，无需创建文件。")
        return

    try:
        fieldnames = ["title", "authors", "publication_date", "abstract", "url", "id"]
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)
        print(f"\n成功! {len(articles)} 篇文章已保存到文件: {os.path.abspath(filename)}")
    except IOError as e:
        print(f"写入文件时发生 I/O 错误: {e}")


def display_articles(articles, keyword=None):
    """
    显示文章列表
    """
    if not articles:
        print("未找到任何文章。")
        return

    print(f"\n找到 {len(articles)} 篇文章:")
    print("-" * 80)

    for i, article in enumerate(articles, 1):
        title = article.get("title", "N/A")
        authors = article.get("authors", "N/A")
        pub_date = article.get("publication_date", "N/A")

        print(f"{i}. 标题: {title}")
        print(f"   作者: {authors}")
        print(f"   发布日期: {pub_date}")
        print(f"   ID: {article.get('id', 'N/A')}")
        print()


if __name__ == "__main__":
    search_keyword = input("请输入搜索关键词 (直接按 Enter 获取所有文章): ").strip()

    # 获取文章
    articles_found = get_articles(search_keyword if search_keyword else None)

    # 显示文章列表
    display_articles(articles_found, search_keyword)

    # 保存到CSV文件
    if articles_found:
        if search_keyword:
            safe_keyword = search_keyword.replace(' ', '_').replace('/', '_')
            output_filename = f"fed_articles_{safe_keyword}.csv"
        else:
            output_filename = "fed_articles_all.csv"
        save_to_csv(articles_found, output_filename)