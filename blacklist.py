class Blacklist:
    # ========== 类别1: 指令覆盖攻击 ==========
    INSTRUCTION_OVERRIDE = {
        "ignore_patterns_cn": [
            "忽略之前", "忽略上述", "忽略以上", "忽略前面",
            "无视之前", "无视上述", "无视以上", "无视前面",
            "不要理会", "不用管", "别管",
            "抛弃之前", "放弃之前",
        ],
        "ignore_patterns_en": [
            "ignore previous", "ignore above", "ignore all",
            "ignore the previous", "ignore the above",
            "disregard previous", "disregard above",
            "forget previous", "forget above",
            "skip previous", "skip above",
        ],
        "new_instruction": [
            "新的指令", "新指令", "新任务", "新的任务",
            "new instruction", "new task", "new command",
            "override instruction", "replace instruction",
            "更新指令", "替换指令",
        ],
    }
    # ========== 类别2: 角色混淆攻击 ==========
    ROLE_CONFUSION = {
        "role_change_cn": [
            "你现在是", "你不再是", "现在你是", "从现在开始你是",
            "你变成", "你改为", "你应该是",
            "假装你是", "扮演", "模拟", "角色扮演",
        ],
        "role_change_en": [
            "you are now", "you're now", "now you are",
            "you are no longer", "you're no longer",
            "act as", "pretend to be", "simulate",
            "role play as", "behave as",
        ],
        "dangerous_roles": [
            "黑客", "hacker", "攻击者", "attacker",
            "无限制", "unrestricted", "不受限",
            "DAN", "do anything now",
            "邪恶", "evil", "恶意",
        ],
    }
    # ========== 类别3: 信息泄露攻击 ==========
    INFORMATION_LEAK = {
        "system_info": [
            "系统提示", "系统提示词", "system prompt",
            "你的指令", "你的提示词", "your instruction",
            "你的规则", "your rules",
            "初始指令", "initial instruction",
            "原始提示", "original prompt",
        ],
        "technical_info": [
            "底层代码", "源代码", "source code",
            "配置信息", "configuration", "config",
            "参数设置", "parameters",
            "模型信息", "model info",
        ],
        "sensitive_info": [
            "密码", "password", "口令",
            "token", "api key", "api_key",
            "secret", "秘钥", "密钥",
            "账号", "account", "用户名", "username",
        ],
        "debug_info": [
            "打印提示词", "print prompt",
            "显示指令", "show instruction",
            "输出配置", "output config",
            "reveal", "expose", "泄露",
        ],
    }
    # ========== 类别4: 越狱攻击 ==========
    JAILBREAK = {
        "jailbreak_keywords": [
            "开发者模式", "developer mode", "dev mode",
            "调试模式", "debug mode",
            "管理员模式", "admin mode",
            "越狱", "jailbreak",
            "绕过", "bypass",
            "突破限制", "break restriction",
        ],
        "jailbreak_prompts": [
            "DAN", "do anything now",
            "STAN", "JailBreak",
            "evil mode", "邪恶模式",
        ],
    }
    # ========== 类别5: 代码注入攻击 ==========
    CODE_INJECTION = {
        "xss_patterns": [
            "<script", "</script>",
            "javascript:",
            "onerror=", "onload=",
        ],
        "sql_patterns": [
            "'; DROP TABLE", "' OR '1'='1",
            "UNION SELECT", "-- ",
        ],
        "command_patterns": [
            "$(", "`", 
            "system(", "exec(",
            "eval(", "import os",
        ],
        "template_injection": [
            "${", "#{", "{{",
            "<%", "%>",
        ],
    }
    # ========== 类别6: 社会工程攻击 ==========
    SOCIAL_ENGINEERING = {
        "authority_impersonation": [
            "我是你的开发者", "i am your developer",
            "我是管理员", "i am admin",
            "我是你的创建者", "i am your creator",
            "紧急情况", "emergency",
            "必须立即", "must immediately",
        ],
        "emotional_manipulation": [
            "求求你", "please please",
            "帮帮我吧", "help me please",
            "这很重要", "this is critical",
        ],
    }

def get_blacklist():
    config = Blacklist()
    blacklist = {
        "instruction_override": config.INSTRUCTION_OVERRIDE,
        "role_confusion": config.ROLE_CONFUSION,
        "information_leak": config.INFORMATION_LEAK,
        "jailbreak": config.JAILBREAK,
        "code_injection": config.CODE_INJECTION,
        "social_engineering": config.SOCIAL_ENGINEERING,
    }
    return blacklist