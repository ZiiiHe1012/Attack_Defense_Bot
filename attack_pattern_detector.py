# 攻击模式检测器 -对于攻击意图进一步识别检测

import re
from typing import Tuple, List, Dict

class AttackPatternDetector:
    """
    检测用户输入中的隐蔽攻击模式
    """
    
    # 攻击动词模式
    ATTACK_VERBS = [
        "进行", "实施", "执行", "发起", "开展",
        "如何做", "怎么做", "怎样做", "如何实现",
        "给我", "提供", "生成", "写一个", "编写"
    ]
    
    # 攻击名词(攻击类型)
    ATTACK_NOUNS = [
        # 直接攻击类型
        "sql注入", "xss", "csrf", "ssrf", "xxe",
        "命令注入", "代码注入", "文件包含", "文件上传",
        "反序列化", "缓冲区溢出", "中间人攻击",
        "dns劫持", "会话劫持", "请求走私",
        
        # 高级攻击
        "供应链攻击", "apt", "零日漏洞", "提权",
        "横向移动", "持久化", "后门",
        
        # 绕过和规避
        "绕过", "bypass", "规避", "躲过", "逃避",
        
        # 数据窃取
        "exfiltrate", "外泄", "窃取", "泄露",
        
        # 恶意软件
        "木马", "病毒", "蠕虫", "勒索软件", "挖矿",
        "僵尸网络", "rootkit",
        
        # 社会工程
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
    
    @classmethod
    def detect_attack_intent(cls, text: str) -> Dict[str, any]:
        """
        检测文本中的攻击意图
        
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
            # 强防御信号,可能不是攻击
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
                # 如果同时包含攻击关键词,则分数更高
                if any(noun in text_lower for noun in cls.ATTACK_NOUNS):
                    patterns_found.append(f"代码请求模式: {pattern}")
                    score += 0.35
        
        # 6. 特殊模式检测
        special_score, special_patterns = cls._detect_special_patterns(text_lower)
        score += special_score
        patterns_found.extend(special_patterns)
        
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
    
    @classmethod
    def _detect_special_patterns(cls, text: str) -> Tuple[float, List[str]]:
        """
        检测特殊的攻击模式
        """
        score = 0.0
        patterns = []
        
        # 编码/加密相关(在攻击上下文中)
        if any(kw in text for kw in ["base64", "url编码", "hex", "unicode"]):
            if any(attack in text for attack in ["payload", "隐藏", "绕过"]):
                score += 0.25
                patterns.append("编码规避模式")
        
        # 内网/内部访问相关
        if any(kw in text for kw in ["内网", "内部", "localhost", "127.0.0.1", "元数据"]):
            if "ssrf" in text or "访问" in text:
                score += 0.3
                patterns.append("内网访问模式")
        
        # 分布式/隐藏来源
        if any(kw in text for kw in ["分布", "多个ip", "代理链", "匿名"]):
            score += 0.25
            patterns.append("分布式攻击模式")
        
        # 数据外泄相关
        if any(kw in text for kw in ["exfiltrate", "外泄", "传输", "发送"]):
            if any(kw in text for kw in ["敏感", "数据", "dns", "隐蔽"]):
                score += 0.3
                patterns.append("数据外泄模式")
        
        # 时序攻击
        if "timing" in text or "侧信道" in text:
            score += 0.2
            patterns.append("侧信道攻击模式")
        
        # 元数据/隐写
        if any(kw in text for kw in ["元数据", "exif", "隐写", "像素"]):
            if "隐藏" in text or "触发" in text:
                score += 0.25
                patterns.append("隐写攻击模式")
        
        return score, patterns
    
    @classmethod
    def should_block(cls, text: str, intent_result: dict = None) -> Tuple[bool, str]:
        """
        综合判断是否应该拦截
        
        Args:
            text: 用户输入
            intent_result: 意图分类结果(可选)
        
        Returns:
            (should_block, reason)
        """
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
            patterns_str = "; ".join(detection["patterns"][:3])  # 只显示前3个
            return True, f"检测到攻击模式 (置信度: {detection['confidence']:.2f}): {patterns_str}"
        
        return False, "未检测到攻击意图"


