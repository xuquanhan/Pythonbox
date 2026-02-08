import requests
import csv
import os

# --- 配置 ---
API_KEY = "2360a68c16b805cf2a02db06372ce22c"
BASE_URL = "https://fedinprint.org/api"
# 每页请求多少条记录，最大值似乎是100
ITEMS_PER_PAGE = 100

def get_articles(keyword=None):
    """
    从 Fed in Print API 获取文章数据。
    如果提供了关键词，则按标题搜索。否则，获取所有文章。
    """
    if keyword:
        print(f"正在搜索关键词为 '{keyword}' 的文章...")
        endpoint = f"{BASE_URL}/item/search"
        params = {"title": keyword}
    else:
        print("准备获取所有文章...")
        endpoint = f"{BASE_URL}/item"
        params = {}

    # 使用 Session 可以复用TCP连接，并保持headers
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
            # 检查请求是否成功
            response.raise_for_status() 
            
            data = response.json()
            print(f"API响应数据结构: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            records = data.get("records", [])

            if not records:
                print("未找到更多记录，获取结束。")
                break

            print(f"Records类型: {type(records)}, 长度: {len(records) if isinstance(records, (list, tuple)) else 'N/A'}")
            if records:
                print(f"第一条记录类型: {type(records[0])}")
                if isinstance(records[0], dict):
                    print(f"第一条记录keys: {list(records[0].keys())}")

            for record in records:
                # 提取作者名字并合并成一个字符串
                # 首先检查record是否为字典
                if not isinstance(record, dict):
                    print(f"警告: record不是字典类型，而是 {type(record)}，内容: {record}")
                    # 如果record不是字典，跳过此记录
                    continue
                
                # 处理author字段可能为列表或字典的情况
                authors_list = record.get("author", [])
                authors = ""
                if isinstance(authors_list, list):
                    # 如果author是列表，遍历每个元素获取名字
                    authors = ", ".join([author.get("name", "") if isinstance(author, dict) else str(author) for author in authors_list])
                elif isinstance(authors_list, dict):
                    # 如果author是字典，直接获取名字
                    authors = authors_list.get("name", "")
                else:
                    # 其他情况，转换为字符串
                    authors = str(authors_list)
                
                # 提取第一个可用的文件链接
                file_url = ""
                if record.get("file"):
                    if isinstance(record["file"], list) and len(record["file"]) > 0:
                        file_url = record["file"][0].get("fileurl", "")
                    else:
                        file_url = str(record["file"]) if "file" in record else ""

                all_articles.append({
                    "title": record.get("title", "N/A"),
                    "authors": authors,
                    "publication_date": record.get("publicationDate", "N/A"), # 注意API返回的字段可能是publicationDate
                    "abstract": record.get("abstract", "N/A"),
                    "url": file_url,
                    "id": record.get("id", "N/A")
                })
            
            page += 1

        except requests.exceptions.HTTPError as e:
            print(f"HTTP 错误: {e}")
            print(f"服务器返回内容: {response.text}")
            break
        except requests.exceptions.RequestException as e:
            print(f"请求发生错误: {e}")
            break
        except ValueError: # JSONDecodeError
            print(f"无法解析返回的 JSON 数据。")
            print(f"服务器返回内容: {response.text}")
            break

    return all_articles

def save_to_csv(articles, filename):
    """将文章列表保存到 CSV 文件。"""
    if not articles:
        print("没有找到任何文章，无需创建文件。")
        return

    try:
        # 定义CSV文件的表头
        fieldnames = ["title", "authors", "publication_date", "abstract", "url", "id"]
        
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(articles)
        print(f"\n成功! {len(articles)} 篇文章已保存到文件: {os.path.abspath(filename)}")

    except IOError as e:
        print(f"写入文件时发生错误: {e}")

if __name__ == "__main__":
    # 1. 获取用户输入
    search_keyword = input("请输入搜索关键词 (直接按 Enter 获取所有文章): ").strip()

    # 2. 调用函数获取数据
    articles_found = get_articles(search_keyword if search_keyword else None)

    # 3. 将结果保存到文件
    if articles_found:
        if search_keyword:
            output_filename = f"fed_articles_{search_keyword.replace(' ', '_')}.csv"
        else:
            output_filename = "fed_articles_all.csv"
        save_to_csv(articles_found, output_filename)
