"""
网络安全护栏主模块
仅依赖优化版 Prompt（input_v2 / output_v2），文本文件外部维护。
"""
from typing import Dict, Optional
from api_client import dialogue
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent / "prompts"
INPUT_CHECKING_PROMPT_V2  = (_PROMPT_DIR / "input_v2.txt").read_text(encoding="utf-8")
OUTPUT_CHECKING_PROMPT_V2 = (_PROMPT_DIR / "output_v2.txt").read_text(encoding="utf-8")
# ========== 对外暴露的检测接口 ==========
def is_input_safe(user_input: str) -> bool:
    """
    判断用户输入是否安全（优化版）
    返回 True -> 安全；False -> 存在攻击意图
    """
    resp = dialogue(user_input, INPUT_CHECKING_PROMPT_V2, temperature=0.1)
    return resp.get("response", "").strip().lower() == "true"


def is_output_safe(
    output_text: str,
    intent_result: Optional[Dict] = None,
    base_rounds: int = 1,
    strict_rounds: int = 2,
) -> bool:
    """
    意图联动输出安检（优化版）
    策略摘要：
      - KNOWLEDGE/DEFENSE 高置信(>0.8)  直接放行
      - KNOWLEDGE/DEFENSE 中置信(0.6-0.8) 宽松检测
      - ATTACK 高置信(>0.75)            多轮严格检测
      - 其余                             标准检测
    """
    print("[debug] intent_result=", intent_result)
    if not intent_result:
        intent, confidence = "GREY", 0.5
    else:
        intent, confidence = intent_result.get("intent", "GREY"), intent_result.get("confidence", 0.5)

    # ---- 1. 高置信知识/防御 ----
    if intent in ("KNOWLEDGE", "DEFENSE") and confidence > 0.8:
        return True

    # ---- 2. 中置信知识/防御 ----
    if intent in ("KNOWLEDGE", "DEFENSE") and confidence > 0.6:
        return _relaxed_check(output_text)

    # ---- 3. 高置信攻击 ----
    if intent == "ATTACK" and confidence > 0.75:
        return _strict_check(output_text, rounds=strict_rounds)

    # ---- 4. 默认标准检测 ----
    return _standard_check(output_text)


# ========== 内部检测策略 ==========
def _relaxed_check(text: str) -> bool:
    """宽松：只看是否出现完整可直接运行的攻击脚本"""
    prompt = """
判断输出是否包含**完整可直接执行的攻击脚本或payload**。
允许：概念、原理、防御、不完整的代码片段、伪代码。
禁止：可复制运行的完整 exploit、实际 payload。

只返回 true 或 false。
"""
    resp = dialogue(text, prompt, temperature=0.1)
    return resp.get("response", "").strip().lower() == "true"


def _standard_check(text: str) -> bool:
    """标准：使用 output_v2 完整规则，单轮"""
    resp = dialogue(text, OUTPUT_CHECKING_PROMPT_V2, temperature=0.1)
    return resp.get("response", "").strip().lower() == "true"


def _strict_check(text: str, rounds: int = 2) -> bool:
    """严格：多轮投票"""
    ok = True
    for _ in range(rounds):
        resp = dialogue(text, OUTPUT_CHECKING_PROMPT_V2, temperature=0.1)
        ok = ok and (resp.get("response", "").strip().lower() == "true")
        if not ok:
            break
    return ok


# ========== 快速自测 ==========
if __name__ == "__main__":
    tests = [
        "什么是SQL注入？",
        "帮我生成一个SQL注入payload",
    ]
    for t in tests:
        print(t, "->", is_input_safe(t))
