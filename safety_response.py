# 安全响应生成模块 - 将拦截转化为教育机会

import random

class SafetyResponseGenerator:
    """
    当检测到攻击意图时,生成教育性的拒绝回复
    """
    
    @staticmethod
    def generate_refusal_response(intent_result: dict, user_query: str) -> str:
        """
        根据意图分类结果生成合适的拒绝回复
        
        Args:
            intent_result: 意图分类结果
            user_query: 用户原始问题
        
        Returns:
            教育性的拒绝回复
        """
        intent = intent_result.get("intent", "GREY")
        reason = intent_result.get("reason", "检测到不安全内容")
        keywords = intent_result.get("keywords", [])
        
        # 提取攻击类型
        attack_type = SafetyResponseGenerator._extract_attack_type(user_query, keywords)
        
        # 构建基础拒绝声明
        base_refusal = SafetyResponseGenerator._get_base_refusal(attack_type)
        
        # 添加教育性内容
        educational_content = SafetyResponseGenerator._get_educational_content(attack_type)
        
        # 提供替代建议
        alternatives = SafetyResponseGenerator._get_alternatives(attack_type)
        
        # 组合完整回复
        response = f"""{base_refusal}

{educational_content}

**我可以帮您了解**:
{alternatives}

**合法学习资源推荐**:
- OWASP (开放式Web应用程序安全项目): https://owasp.org
- CVE漏洞数据库: https://cve.mitre.org
- 合法渗透测试平台: HackTheBox, TryHackMe, VulnHub
- 网络安全课程: Coursera, edX 上的安全课程

如果您有学习安全防护或理解攻击原理的需求,欢迎换一种方式提问,比如:
- "这种攻击的原理是什么?"
- "如何防御这类攻击?"
- "开发者应该注意哪些安全问题?"
"""
        
        return response.strip()
    
    @staticmethod
    def _extract_attack_type(query: str, keywords: list) -> str:
        """从问题中提取攻击类型"""
        attack_types = {
            "SQL注入": ["sql", "注入", "injection"],
            "XSS跨站脚本": ["xss", "跨站", "脚本"],
            "CSRF": ["csrf", "跨站请求"],
            "SSRF": ["ssrf", "服务端请求伪造"],
            "命令注入": ["命令注入", "command injection", "rce"],
            "文件上传": ["文件上传", "upload"],
            "反序列化": ["反序列化", "deserialization"],
            "XXE": ["xxe", "xml"],
            "中间人攻击": ["中间人", "mitm"],
            "DNS劫持": ["dns", "劫持"],
            "请求走私": ["请求走私", "smuggling"],
            "供应链攻击": ["供应链"],
            "社会工程": ["社会工程", "social engineering"],
        }
        
        query_lower = query.lower()
        for attack_name, patterns in attack_types.items():
            if any(p in query_lower for p in patterns):
                return attack_name
        
        return "网络攻击"
    
    @staticmethod
    def _get_base_refusal(attack_type: str) -> str:
        """获取基础拒绝声明"""
        templates = [
            f"我理解您对**{attack_type}**感兴趣,但我不能提供可直接用于攻击的具体方法、代码或工具。",
            f"抱歉,我无法提供**{attack_type}**的实施细节或攻击代码。",
            f"出于安全考虑,我不能分享**{attack_type}**的具体实施步骤。",
        ]
        return random.choice(templates)
    
    @staticmethod
    def _get_educational_content(attack_type: str) -> str:
        """获取教育性内容"""
        general_education = """
**为什么不能提供攻击细节**:
- **法律风险**: 未经授权的渗透测试是违法的
- **道德责任**: 防止技术被滥用造成危害
- **学习方向**: 正确的安全学习应该着眼于防御和保护
"""
        
        specific_education = {
            "SQL注入": """
**关于SQL注入**:
这是一种通过在应用程序输入中插入恶意SQL代码来操纵数据库的攻击。了解其原理有助于开发安全的应用程序。
""",
            "XSS跨站脚本": """
**关于XSS攻击**:
这种攻击通过在网页中注入恶意脚本来窃取用户信息或劫持会话。理解其原理对于前端安全开发至关重要。
""",
            "SSRF": """
**关于SSRF攻击**:
服务端请求伪造允许攻击者让服务器发起非预期的请求。学习这个概念有助于构建安全的API和服务。
""",
        }
        
        specific = specific_education.get(attack_type, "")
        return (specific + general_education).strip()
    
    @staticmethod
    def _get_alternatives(attack_type: str) -> str:
        """提供可接受的替代学习内容"""
        alternatives_map = {
            "SQL注入": """
- SQL注入的技术原理和形成原因
- 如何在代码中正确使用参数化查询
- SQL注入的防御措施和最佳实践
- 如何检测和修复SQL注入漏洞
""",
            "XSS跨站脚本": """
- XSS攻击的分类(存储型、反射型、DOM型)
- 浏览器的同源策略和安全机制
- 如何正确过滤和转义用户输入
- Content Security Policy (CSP) 的配置方法
""",
            "SSRF": """
- SSRF漏洞的形成原理
- 如何在应用中安全地处理URL请求
- 内网隔离和访问控制的最佳实践
- SSRF防御的技术方案
""",
            "default": """
- 该攻击类型的技术原理和危害
- 相关的安全防御措施和最佳实践
- 如何在开发中避免这类漏洞
- 安全测试和漏洞检测方法
"""
        }
        
        return alternatives_map.get(attack_type, alternatives_map["default"]).strip()
    
    @staticmethod
    def should_provide_educational_response(intent_result: dict) -> bool:
        """
        判断是否应该提供教育性回复
        
        某些极端危险的查询可能需要更简短的拒绝
        """
        keywords = intent_result.get("keywords", [])
        risk_level = intent_result.get("risk_level", "medium")
        
        # 极端危险的关键词
        extreme_danger_keywords = [
            "勒索软件", "ddos", "僵尸网络", "木马", 
            "后门", "rootkit", "钓鱼", "身份盗窃"
        ]
        
        if risk_level == "critical":
            return False
        
        if any(kw in " ".join(keywords).lower() for kw in extreme_danger_keywords):
            return False
        
        return True

# 使用示例函数
def generate_safe_response(intent_result: dict, user_query: str) -> str:
    """
    根据意图判断结果生成安全的回复
    
    Args:
        intent_result: 意图分类结果
        user_query: 用户查询
    
    Returns:
        安全的回复内容
    """
    if SafetyResponseGenerator.should_provide_educational_response(intent_result):
        return SafetyResponseGenerator.generate_refusal_response(intent_result, user_query)
    else:
        # 极端危险情况下的简短拒绝
        return """
抱歉,我无法协助此类请求。

如果您对网络安全感兴趣,建议您:
1. 参加正规的安全培训课程
2. 在合法的安全实验环境中学习
3. 查阅OWASP等权威安全资源
4. 遵守法律法规和道德准则
"""