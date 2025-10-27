from blacklist import get_blacklist
from safety_agent import is_input_safe, is_output_safe

def validate_user_input(user_input):
    blacklist = get_blacklist()
    user_input_lower = user_input.lower()
    
    # 正确遍历嵌套字典结构
    for category, pattern_groups in blacklist.items():
        for pattern_type, patterns in pattern_groups.items():
            for pattern in patterns:
                if pattern.lower() in user_input_lower:
                    return False, f"触发黑名单: {category}/{pattern_type} - '{pattern}'"
    
    return True, "通过黑名单检测"


def validate_user_input_smart(user_input):
    """
    智能黑名单：只检查高危组合模式
    """
    user_input_lower = user_input.lower()
    
    # 高危组合模式
    high_risk_combinations = [
        # 指令覆盖攻击组合
        [["忽略", "无视", "不要理会"], ["之前", "上述", "以上", "前面"]],
        [["ignore", "disregard", "forget"], ["previous", "above", "all"]],
        [["新的", "new", "替换", "replace"], ["指令", "instruction", "任务", "task"]],
        
        # 角色混淆 + 危险角色
        [["你现在是", "你不再是", "假装你是", "you are now", "act as"], 
         ["黑客", "hacker", "攻击者", "attacker", "无限制", "unrestricted"]],
        
        # 信息泄露请求
        [["告诉我", "显示", "打印", "输出", "reveal", "show", "print"], 
         ["系统提示", "提示词", "指令", "system prompt", "instruction", "规则", "rules"]],
        
        # 代码注入特征
        [["<script", "javascript:", "onerror=", "$(", "eval("], []],  # 单独出现就拦截
    ]
    
    # 检查组合模式
    for combination in high_risk_combinations:
        if len(combination) == 1:  # 单个模式即拦截
            if any(pattern in user_input_lower for pattern in combination[0]):
                return False, f"检测到高危模式: {combination[0][0]}"
        else:  # 需要组合出现
            group1_match = any(pattern in user_input_lower for pattern in combination[0])
            group2_match = any(pattern in user_input_lower for pattern in combination[1])
            if group1_match and group2_match:
                return False, f"检测到高危组合: {combination[0][0]} + {combination[1][0]}"
    
    return True, "通过智能黑名单检测"


def validate_prompt(prompt):
    """
    prompt验证函数
    """
    if not is_input_safe(prompt):
        return False
    if not is_output_safe(prompt):
        return False
    return True
