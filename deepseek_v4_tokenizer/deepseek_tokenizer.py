import os
import transformers

# 用脚本所在目录，避免路径问题
script_dir = os.path.dirname(os.path.abspath(__file__))

tokenizer = transformers.AutoTokenizer.from_pretrained(
    script_dir, trust_remote_code=True
)

# 添加输入提示，接收用户手动输入的文本
text = input("请输入要计算 Token 的文本：")

if text.strip() == "":
    print("输入为空，未进行 Token 计算。")
else:
    result = tokenizer.encode(text)
    print("Token IDs:", result)
    print("Token 数量:", len(result))

input("按回车键退出...")