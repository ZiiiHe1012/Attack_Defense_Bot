# 意图识别模块

import json
from api_client import dialogue

INTENT_CLASSIFICATION_PROMPT_V2 = """
你是一个高级安全意图分类器。你的任务是准确判断用户的真实意图,特别注重区分**学习防御**和**实施攻击**。

**核心判断标准**:

1. **知识学习**(KNOWLEDGE): 询问概念、原理、技术介绍(不涉及具体实施)
   特征:S
   - 关键词: "什么是"、"原理"、"介绍"、"定义"、"概念"
   - 询问攻击的危害、影响、历史
   - 不要求具体代码、payload或实施步骤

2. **防御实践**(DEFENSE): 请求防护方法、安全编码、漏洞修复
   特征:
   - 关键词: "如何防御"、"防止"、"加固"、"安全地"、"保护"、"检测"、"审计"
   - 询问最佳实践、安全配置、防护措施
   - 着眼于保护系统而非攻击系统
   - **重点**: 即使提到攻击技术,如果目的是防御,则归为DEFENSE

3. **攻击实施**(ATTACK): 请求具体攻击方法、工具、代码、bypass技巧
   特征:
   - 关键词: "如何进行"、"给我示例"、"生成payload"、"绕过"、"实现攻击"
   - 询问具体攻击步骤、exploit代码、攻击工具使用
   - 隐藏意图: "编码隐藏"、"规避检测"、"伪装"、"exfiltrate"
   - 询问如何实施而非如何防御
   - **关键区分**: 
     * "如何进行XX攻击" → ATTACK
     * "如何防御XX攻击" → DEFENSE
     * "XX攻击的原理" → KNOWLEDGE

4. **灰色地带**(GREY): 意图不明确或包含合法声明但请求危险内容
   特征:
   - 声称研究/教学用途但请求攻击细节
   - 同时包含防御和攻击元素
   - 提问方式模糊,难以判断意图

**攻击意图的隐蔽表达识别**:
以下表达通常暗示攻击意图:
- "规避检测"、"绕过"、"躲过"、"隐藏"、"伪装"
- "exfiltrate"、"数据外泄"、"窃取"
- "payload"、"exploit"、"shellcode"
- "分片"、"编码链"、"混淆"(用于逃避检测的场景)
- "触发"、"执行"(在非防御上下文中)

**判断流程**:
1. 检查是否明确询问"如何防御/防止/检测" → 优先考虑DEFENSE
2. 检查是否仅询问概念/原理(无实施细节) → 考虑KNOWLEDGE
3. 检查是否请求具体攻击方法/代码/工具 → 判定为ATTACK
4. 检查是否包含隐蔽攻击意图的关键词 → 判定为ATTACK
5. 其他难以判断的 → GREY

**输出格式**(必须是合法JSON):
{
  "intent": "KNOWLEDGE/ATTACK/DEFENSE/GREY",
  "confidence": 0.85,
  "reason": "判断理由(50字内)",
  "keywords": ["关键词1", "关键词2"],
  "risk_level": "low/medium/high"
}

**示例**:

输入: "如何设置强密码保护账号安全"
输出: {"intent": "DEFENSE", "confidence": 0.95, "reason": "询问安全防护措施", "keywords": ["设置", "保护", "安全"], "risk_level": "low"}

输入: "如何进行中间人攻击"
输出: {"intent": "ATTACK", "confidence": 0.98, "reason": "请求具体攻击实施方法", "keywords": ["如何进行", "中间人攻击"], "risk_level": "high"}

输入: "给我一个SSRF攻击的示例"
输出: {"intent": "ATTACK", "confidence": 0.97, "reason": "请求攻击示例代码", "keywords": ["给我", "示例", "SSRF攻击"], "risk_level": "high"}

输入: "如何防御XSS攻击"
输出: {"intent": "DEFENSE", "confidence": 0.96, "reason": "询问防御方法", "keywords": ["如何防御", "XSS"], "risk_level": "low"}

输入: "SQL注入的原理是什么"
输出: {"intent": "KNOWLEDGE", "confidence": 0.93, "reason": "询问技术原理", "keywords": ["原理", "SQL注入"], "risk_level": "low"}

输入: "如何把payload做base64编码后隐藏在参数里"
输出: {"intent": "ATTACK", "confidence": 0.96, "reason": "询问规避检测的攻击技巧", "keywords": ["payload", "编码", "隐藏"], "risk_level": "high"}

输入: "API密钥的安全管理方法"
输出: {"intent": "DEFENSE", "confidence": 0.94, "reason": "询问安全管理最佳实践", "keywords": ["安全管理", "API密钥"], "risk_level": "low"}

输入: "如何在代码审计中发现恶意注释"
输出: {"intent": "DEFENSE", "confidence": 0.92, "reason": "询问安全审计方法", "keywords": ["代码审计", "发现", "恶意"], "risk_level": "low"}

**重要**: 只返回JSON,不要有其他文字。

现在分析以下用户输入:
"""

def classify_intent_v2(user_input: str) -> dict:
    """
    意图分类函数
    """
    try:
        response = dialogue(
            user_input=user_input,
            custom_prompt=INTENT_CLASSIFICATION_PROMPT_V2,
            temperature=0.1
        )
        result_text = response.get("response", "").strip()
        
        # 提取JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        
        # 确保包含risk_level字段
        if "risk_level" not in result:
            result["risk_level"] = "medium"
        
        return result
    except Exception as e:
        print(f"意图识别失败: {e}")
        return {
            "intent": "GREY",
            "confidence": 0.5,
            "reason": f"解析失败: {str(e)}",
            "keywords": [],
            "risk_level": "medium"
        }

def validate_by_intent_v2(user_input: str) -> tuple:
    """
    意图验证函数
    Returns:
        (bool/str, str/dict): 
            - (True, "原因") - 直接放行
            - (False, "原因") - 直接拦截
            - ("CONTINUE", intent_result) - 需要进一步AI检测
    """
    intent_result = classify_intent_v2(user_input)
    intent = intent_result.get("intent", "GREY")
    confidence = intent_result.get("confidence", 0.5)
    risk_level = intent_result.get("risk_level", "medium")
    
    # 知识学习: 高置信度直接放行
    if intent == "KNOWLEDGE" and confidence > 0.85:
        return True, f"意图: 知识学习 (置信度: {confidence:.2f})"
    
    # 防御实践: 中高置信度直接放行
    if intent == "DEFENSE" and confidence > 0.80:
        return True, f"意图: 防御实践 (置信度: {confidence:.2f})"
    
    # 攻击实施: 高置信度或高风险直接拦截
    if intent == "ATTACK":
        if confidence > 0.85 or risk_level == "high":
            reason = intent_result.get("reason", "检测到攻击意图")
            return False, f"意图: 攻击实施 - {reason}"
        # 中等置信度进入AI检测
        elif confidence > 0.65:
            return "CONTINUE", intent_result
    
    # 灰色地带或低置信度: 进入AI检测
    return "CONTINUE", intent_result
