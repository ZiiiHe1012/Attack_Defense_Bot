import requests
import json
import re
from typing import List, Dict, Optional
from pathlib import Path

class KnowledgeBaseBuilder:
    # 知识库构建类
    def __init__(self, token: str, base_url: str = "http://10.1.0.220:9002"):
        self.token = token
        self.base_url = base_url
    
    def create_database(self, database_name: str, metric_type: str = "COSINE") -> dict:
        # 创建向量数据库
        url = f"{self.base_url}/api/databases"
        payload = {
            "token": self.token,
            "database_name": database_name,
            "metric_type": metric_type
        }
        response = requests.post(url, json=payload)
        # 检查响应状态
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return {"status": "error", "message": response.text}
        try:
            return response.json()
        except Exception as e:
            print(f"JSON解析错误: {e}")
            print(f"Response text: {response.text}")
            return {"status": "error", "message": str(e)}
    
    def list_databases(self) -> dict:
        # 列出所有数据库
        url = f"{self.base_url}/api/databases"
        response = requests.get(url, params={"token": self.token})
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return {"status": "error", "message": response.text}
        try:
            return response.json()
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return {"status": "error", "message": str(e)}
    
    def upload_files(self, database_name: str, files: List[Dict]) -> dict:
        # 批量上传文件到数据库
        url = f"{self.base_url}/api/databases/{database_name}/files"
        payload = {
            "token": self.token,
            "files": files
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return {"status": "error", "message": response.text}
        try:
            return response.json()
        except Exception as e:
            print(f"JSON解析错误: {e}")
            return {"status": "error", "message": str(e)}

def split_by_paragraph(text: str, min_length: int = 100) -> List[str]:
    """
    按段落分块文本
    Args:
        text: 原始文本
        min_length: 最小段落长度,小于此长度的段落会合并
    Returns:
        段落列表
    """
    # 按双换行符或单换行符分割
    paragraphs = re.split(r'\n\s*\n|\n', text)
    # 清理空白段落
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    # 合并过短的段落
    merged = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) < min_length:
            buffer += para + "\n"
        else:
            if buffer:
                merged.append(buffer.strip())
            buffer = para + "\n"
    if buffer:
        merged.append(buffer.strip())
    return merged

def load_json_dataset(file_path: str, text_field: str = "text") -> List[Dict]:
    """
    加载JSON格式数据集
    Args:
        file_path: JSON文件路径
        text_field: 文本字段名
    Returns:
        格式化的文件列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    files = []
    if isinstance(data, list):
        for item in data:
            if text_field in item:
                files.append({
                    "file": item[text_field],
                    "metadata": {k: v for k, v in item.items() if k != text_field}
                })
    return files

def load_markdown_file(file_path: str, metadata: Optional[Dict] = None) -> List[Dict]:
    """
    加载Markdown文件,按标题和段落分块
    Args:
        file_path: Markdown文件路径
        metadata: 可选的元数据
    Returns:
        格式化的文件列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 按标题分割
    sections = re.split(r'(^#{1,6}\s+.+$)', content, flags=re.MULTILINE)
    files = []
    current_title = ""
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        # 检查是否是标题
        if re.match(r'^#{1,6}\s+', section):
            current_title = section.strip()
        else:
            # 分段落
            paragraphs = split_by_paragraph(section)
            for para in paragraphs:
                file_metadata = metadata or {}
                file_metadata.update({
                    "source": Path(file_path).name,
                    "section": current_title
                })  
                files.append({
                    "file": para,
                    "metadata": file_metadata
                })
    return files

"""
ATT_CK库中收集了303条ics-attack与mobile-attack技术数据, 907条enterprise-attack技术数据, 共1210条技术数据
这些数据从约80万行的JSON文件中提取, 包含技术描述、战术、平台等信息

D3FEND库中收集了3224条防御技术数据
这些数据从约10万行的JSON文件中提取, 包含防御技术的定义、类别等信息

ATT&CK + D3FEND 知识库完整的覆盖了攻击与防御的各个方面, 可用于构建性能更佳的的网络安全问答系统

OWASP CheatSheet Series包含大量Web安全最佳实践, 覆盖输入验证、认证授权、会话管理、加密等多个方面
OWASP库中从一百多个md文件中清洗并收集了2427段内容，充实了网络安全知识库

"CyberMetric: A Benchmark Dataset based on Retrieval-Augmented Generation for Evaluating LLMs in Cybersecurity Knowledge"
IEEE CSR 2024的一篇文章，一个基于检索增强生成的基准数据集，用于评估大型语言模型在网络安全知识方面的能力
其中包含了大量网络安全相关的问答对，拿过来用用（https://github.com/cybermetric）
"""