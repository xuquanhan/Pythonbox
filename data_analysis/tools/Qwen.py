
import os
from openai import OpenAI

def main():
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        api_key="sk-369567c528b54143950e25f3f3243e05",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    # 初始化对话历史
    messages = [
        {'role': 'system', 'content': '你是一个专业的交易员，同时你也是一个黄金分析师，特别具备宏观视野。'
                                      '在回答任何问题前，先上网检查最新的系统时间并将系统时间带入到用户的问题中去，例如用户说当前或这类表示现在的时间，指代的就是当前的系统时间。'
                                      '所以如果用户所询问的关于当前的任何问题不在你的知识库的时间范围里面，请你上网搜索并更新最新内容。'
                                      '注意回答问题用词简洁，不用过多回答超出用户询问范围外的内容，但是每一步相关的操作一定要给到细节到位。'
                                      '如果要超出问题范围的内容要补充，一定先跟用户确认'}
    ]
    
    print("欢迎使用黄金市场分析助手！请输入您的问题(输入'quit'退出)：")
    
    while True:
        # 获取用户输入
        user_input = input(">>> ")
        
        # 检查是否退出
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("感谢使用，再见！")
            break
        
        # 将用户消息添加到对话历史
        messages.append({'role': 'user', 'content': user_input})
        
        # 判断是否需要启用搜索功能
        enable_search = any(keyword in user_input.lower() for keyword in [
            '最新', '当前', '现在', '近期', '最近', '今天', '明天', '未来', '预测', 
            '行情', '趋势', '数据', '新闻'
        ])
        
        try:
            # 调用模型API
            completion = client.chat.completions.create(
                model="qwen3-max",
                messages=messages,
                extra_body={"enable_search": enable_search} if enable_search else None
            )
            
            # 获取模型回复
            response = completion.choices[0].message.content
            print(f"Assistant: {response}\n")
            
            # 将助手回复添加到对话历史
            messages.append({'role': 'assistant', 'content': response})
            
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()