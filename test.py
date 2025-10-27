"""
测试API是否支持流式输出
"""
import requests
import json

url = "http://10.1.0.220:9002/api/dialogue"
token = "jI3sZMsJLctmIl87PAEQNeRq6NE9ymyx7M-rVk_MOWWA-kNbPDx-o8nAG0UUsmC-"

# 测试1: 尝试stream=True参数
print("=" * 60)
print("测试1: 尝试 stream=True 参数")
print("=" * 60)

try:
    response = requests.post(
        url,
        json={
            "token": token,
            "user_input": "请简单介绍一下Python编程语言",
            "stream": True  # 尝试请求流式输出
        },
        stream=True,  # 客户端以流式接收
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print()
    
    # 检查是否是流式响应
    if 'text/event-stream' in response.headers.get('Content-Type', ''):
        print("✓ API支持流式输出 (SSE格式)")
        print("\n接收到的流式数据：")
        print("-" * 60)
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                print(decoded)
                
    elif response.headers.get('Transfer-Encoding') == 'chunked':
        print("✓ API支持流式输出 (chunked格式)")
        print("\n接收到的流式数据：")
        print("-" * 60)
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                print(chunk.decode('utf-8'), end='', flush=True)
                
    else:
        print("✗ 看起来是普通响应，不是流式")
        print(f"响应内容: {response.text[:200]}...")
        
except Exception as e:
    print(f"✗ 测试失败: {e}")

print("\n")

# 测试2: 检查响应中是否有stream相关字段
print("=" * 60)
print("测试2: 查看正常响应的结构")
print("=" * 60)

try:
    response = requests.post(
        url,
        json={
            "token": token,
            "user_input": "你好"
        }
    )
    
    result = response.json()
    print("响应的所有字段：")
    for key in result.keys():
        print(f"  - {key}")
    
    print("\n完整响应结构：")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    
except Exception as e:
    print(f"✗ 测试失败: {e}")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)
print("""
如果测试1显示 "✓ API支持流式输出"：
  → 可以使用真正的流式输出
  → 需要修改 api_client.py 支持流式接收
  
如果测试1显示 "✗ 看起来是普通响应"：
  → API不支持流式输出
  → 只能在前端模拟流式效果（逐字显示）
""")