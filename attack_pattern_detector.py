import re
from typing import Tuple, List, Dict, Optional

class AttackPatternDetector:
    # 检测用户输入中的隐蔽攻击模式
    # 攻击动词模式
    ATTACK_VERBS = [
        "进行", "实施", "执行", "发起", "开展",
        "如何做", "怎么做", "怎样做", "如何实现",
        "给我", "提供", "生成", "写一个", "编写"
    ]
    # 攻击名词
    ATTACK_NOUNS = [
        "sql注入", "xss", "csrf", "ssrf", "xxe",
        "命令注入", "代码注入", "文件包含", "文件上传",
        "反序列化", "缓冲区溢出", "中间人攻击",
        "dns劫持", "会话劫持", "请求走私",
        "供应链攻击", "apt", "零日漏洞", "提权",
        "横向移动", "持久化", "后门",
        "绕过", "bypass", "规避", "躲过", "逃避",
        "exfiltrate", "外泄", "窃取", "泄露",
        "木马", "病毒", "蠕虫", "勒索软件", "挖矿",
        "僵尸网络", "rootkit",
        "钓鱼", "社会工程", "凭证填充"
    ]
    # 规避检测的模式
    EVASION_PATTERNS = [
        "隐藏", "伪装", "混淆", "编码",
        "分片", "拆分", "分布",
        "隐写", "隐蔽", "掩盖",
        "绕过waf", "绕过防火墙", "绕过检测",
        "逃避检测", "规避监控"
    ]
    # Payload相关
    PAYLOAD_PATTERNS = [
        "payload", "exploit", "shellcode",
        "poc", "exp", "攻击载荷",
        "攻击向量", "攻击代码"
    ]
    # 示例和代码请求
    CODE_REQUEST_PATTERNS = [
        r"给.*示例", r"给.*代码", r"写.*代码",
        r"生成.*脚本", r"提供.*工具",
        r"示例代码", r"代码示例", r"具体.*代码"
    ]
    # 防御关键词(用于区分防御和攻击)
    DEFENSE_KEYWORDS = [
        "防御", "防止", "防护", "保护",
        "加固", "安全", "检测", "发现",
        "修复", "补丁", "审计", "监控",
        "最佳实践", "安全编码", "安全配置"
    ]

    def detect_attack_intent(cls, text: str) -> Dict[str, any]:
        """
        检测文本中的攻击意图
        Args:
            text: 用户输入文本
        Returns:
            {
                "is_attack": bool,
                "confidence": float,
                "patterns": list,
                "explanation": str
            }
        """
        text_lower = text.lower()
        patterns_found = []
        score = 0.0
        # 1. 检查是否是防御性问题
        defense_count = sum(1 for kw in cls.DEFENSE_KEYWORDS if kw in text_lower)
        if defense_count >= 2:
            return {
                "is_attack": False,
                "confidence": 0.1,
                "patterns": [],
                "explanation": "检测到防御性意图关键词"
            }
        # 2. 检查攻击动词 + 攻击名词组合
        for verb in cls.ATTACK_VERBS:
            if verb in text_lower:
                for noun in cls.ATTACK_NOUNS:
                    if noun in text_lower:
                        patterns_found.append(f"攻击模式: {verb} + {noun}")
                        score += 0.4
        # 3. 检查规避检测模式
        for pattern in cls.EVASION_PATTERNS:
            if pattern in text_lower:
                patterns_found.append(f"规避模式: {pattern}")
                score += 0.3
        # 4. 检查Payload相关
        for pattern in cls.PAYLOAD_PATTERNS:
            if pattern in text_lower:
                patterns_found.append(f"Payload关键词: {pattern}")
                score += 0.3
        # 5. 检查代码/示例请求
        for pattern in cls.CODE_REQUEST_PATTERNS:
            if re.search(pattern, text_lower):
                if any(noun in text_lower for noun in cls.ATTACK_NOUNS):
                    patterns_found.append(f"代码请求模式: {pattern}")
                    score += 0.35
        # 计算置信度(归一化到0-1)
        confidence = min(score, 1.0)
        # 判断是否为攻击
        is_attack = confidence >= 0.5
        # 生成解释
        if is_attack:
            explanation = f"检测到 {len(patterns_found)} 个攻击特征模式"
        else:
            explanation = "未检测到明显攻击意图"
        return {
            "is_attack": is_attack,
            "confidence": confidence,
            "patterns": patterns_found,
            "explanation": explanation
        }
    
    def should_block(cls, text: str, intent_result: Optional[Dict] = None) -> Tuple[bool, str]:
        # 综合判断是否应该拦截
        detection = cls.detect_attack_intent(text)
        # 如果有意图分类结果,综合考虑
        if intent_result:
            intent = intent_result.get("intent", "GREY")
            intent_confidence = intent_result.get("confidence", 0.5)
            # 如果意图分类已经判定为ATTACK且高置信度
            if intent == "ATTACK" and intent_confidence > 0.85:
                return True, f"意图分类判定为攻击 (置信度: {intent_confidence:.2f})"
            # 如果意图分类判定为DEFENSE
            if intent == "DEFENSE" and intent_confidence > 0.80:
                return False, "意图分类判定为防御"
        # 基于模式检测结果
        if detection["is_attack"]:
            patterns_str = "; ".join(detection["patterns"][:3])
            return True, f"检测到攻击模式 (置信度: {detection['confidence']:.2f}): {patterns_str}"
        return False, "未检测到攻击意图"


def validate_by_pattern(user_input: str, intent_result: Optional[Dict] = None) -> Tuple[bool, str]:
    # 基于攻击模式的验证
    should_block, reason = AttackPatternDetector.should_block(user_input, intent_result)
    if should_block:
        return False, f"攻击模式检测未通过: {reason}"
    return True, "通过攻击模式检测"