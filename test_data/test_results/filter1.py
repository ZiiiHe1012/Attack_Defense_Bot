import json

# 读取文件
with open("failed_cases_simplified.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 筛选出 actual_block 为 False 的项（漏放）
filtered = [case for case in data if case.get("actual_block") is False]

# 输出或保存结果
print(json.dumps(filtered, ensure_ascii=False, indent=2))

# 如果想保存：
with open("missed_cases.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)
