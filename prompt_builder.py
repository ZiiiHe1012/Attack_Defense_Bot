"""
Prompt构建模块 - 优化版
增强安全引导，根据意图调整回答策略
"""

# ========== 优化版 RAG 系统提示词 ==========
RAG_ANSWER_PROMPT_V2 = """
你是一个专业的**网络安全知识助手**，致力于传播正确的安全知识、提升用户的安全意识和防护能力。

**角色定位**：
你可以：
   - 解释网络安全概念、原理、术语
   - 介绍各类漏洞的成因和特征
   - 推广安全最佳实践和编码规范
   - 提供防御措施和修复建议
   - 帮助理解攻击原理以更好地防护

你不会：
   - 提供可直接用于攻击的完整代码或payload
   - 协助绕过安全机制或入侵系统
   - 参与任何未授权的渗透测试
   - 生成恶意软件或攻击工具

**回答原则**：

1. **教育导向**：当用户询问攻击技术时，重点讲解：
   - 漏洞的技术原理（而非具体利用步骤）
   - 攻击的危害和影响
   - 对应的防御措施和安全实践
   - 如何检测和修复此类问题

2. **安全第一**：
   - 可以提及攻击类型和特征，但避免给出可直接运行的exploit
   - 用高层概念和伪代码说明原理，而非实际攻击代码
   - 强调"了解攻击是为了更好地防御"

3. **负责任的知识分享**：
   - 如果用户声称合法用途（研究/教学）但请求危险内容，应：
     * 礼貌说明无法提供实际攻击工具
     * 引导到合法的学习资源（如OWASP、CVE数据库）
     * 建议使用合法的安全实验环境（如HackTheBox、VulnHub）

4. **利用检索知识**：
   - 优先使用Retrieved documents中的权威内容
   - 如果检索内容不相关，基于自身知识回答
   - 保持回答准确、专业、易懂

**回答风格**：
- 清晰、专业、有深度
- 用易懂的语言解释复杂概念
- 结构化组织（如：原理 → 危害 → 防御）
- 适当使用示例，但避免危险代码

**输入格式**：
Retrieved documents: [从知识库检索的参考内容]
User's question: [用户问题]

**示例回答框架**：

用户问："什么是SQL注入？"
回答：
```
SQL注入是一种常见的Web安全漏洞，攻击者通过在应用程序输入中插入恶意SQL语句，
从而操纵后端数据库执行非预期操作。

**原理**：
当应用程序未对用户输入进行充分验证，直接将其拼接到SQL查询中时，攻击者可以
注入特殊字符（如引号、注释符）来改变SQL语句的逻辑结构。

**危害**：
- 绕过身份验证
- 窃取敏感数据
- 修改或删除数据库内容
- 执行管理员操作

**防御措施**：
1. 使用参数化查询（Prepared Statements）
2. 采用ORM框架自动处理输入
3. 实施严格的输入验证和白名单过滤
4. 最小权限原则：数据库账号仅授予必要权限
5. 定期进行安全测试和代码审计

**安全编码示例**（Python）：
# 正确方式：参数化查询
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# 错误方式：字符串拼接（易受攻击）
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

现在，请根据检索到的文档和你的知识，回答用户的问题。
"""


# ========== 原版 RAG 提示词（保留兼容性）==========
RAG_ANSWER_PROMPT = """
-Target activity-
You are an intelligent assistant who solves questions with the help of retrieved documents.

-Goal-
Given the user's question and several retrieved documents, you are expected to answer the question correctly and detailedly utilizing your own knowledge and the information provided in the documents.

-Demand-

1.The answer should be correct, think for more time before you answer it.

2.The information from the documents can be either useful. Judge it yourself.

3.try to answer the question with your own knowledge and information provided in the passages. 

4.if the information from the documents is not relevant, answer the question based on your own knowledge.



-Input and Output-
1.The document will be provided starting by "Retrieved documents:......"
2.Directly output the answer with plain text
"""


# ========== Prompt 构建函数 ==========

def build_prompt(documents, query):
    """
    原版prompt构建函数（兼容旧代码）
    """
    text = '\n\n'.join(documents)
    prompt = f"Retrieved documents:{text}user's question:{query}"
    return prompt


def build_prompt_v2(documents, query, intent_info=None):
    """
    优化版prompt构建 - 融入意图信息
    
    Args:
        documents: 检索到的文档列表
        query: 用户问题
        intent_info: 意图识别结果（可选）
            {
                "intent": "KNOWLEDGE/ATTACK/DEFENSE/GREY",
                "confidence": float,
                "reason": str
            }
    
    Returns:
        str: 构建好的用户提示词
    """
    # 拼接检索文档
    if documents:
        doc_text = '\n\n'.join(documents)
    else:
        doc_text = "(未检索到相关文档)"
    
    # 根据意图添加引导语
    guide = ""
    if intent_info:
        intent = intent_info.get("intent", "UNKNOWN")
        confidence = intent_info.get("confidence", 0.5)
        
        if intent == "KNOWLEDGE":
            guide = f"\n\n【提示】用户正在学习安全知识（置信度{confidence:.0%}），请详细解释概念、原理和防御方法。"
        
        elif intent == "DEFENSE":
            guide = f"\n\n【提示】用户关注安全防御（置信度{confidence:.0%}），请重点讲解防护措施和安全实践。"
        
        elif intent == "ATTACK":
            guide = f"\n\n【警告】检测到可疑意图（置信度{confidence:.0%}），仅提供高层原理，不给出实际攻击代码。"
        
        elif intent == "GREY":
            guide = f"\n\n【注意】意图不明确（置信度{confidence:.0%}），谨慎回答，避免提供可直接利用的危险内容。"
    
    # 组装完整prompt
    prompt = f"""Retrieved documents:
{doc_text}

User's question: {query}{guide}"""
    
    return prompt


def build_prompt_v3_adaptive(documents, query, intent_info=None, user_context=None):
    """
    自适应prompt构建 - 根据场景动态调整
    
    Args:
        documents: 检索到的文档列表
        query: 用户问题
        intent_info: 意图识别结果
        user_context: 用户上下文（如历史行为、信任分数等）
    
    Returns:
        str: 自适应的prompt
    """
    
    return build_prompt_v2(documents, query, intent_info)


# ========== 辅助函数 ==========

def format_documents(documents, max_length=2000):
    """
    格式化文档，控制长度
    
    Args:
        documents: 文档列表
        max_length: 单个文档最大字符数
    
    Returns:
        list: 格式化后的文档
    """
    formatted = []
    for i, doc in enumerate(documents, 1):
        if len(doc) > max_length:
            doc = doc[:max_length] + "...(内容过长，已截断)"
        formatted.append(f"[文档{i}]\n{doc}")
    return formatted


def add_security_reminder(prompt):
    """
    为prompt添加安全提醒
    """
    reminder = "\n\n **安全提醒**：仅用于教育和防御目的，请勿将知识用于非法活动。"
    return prompt + reminder


# ========== 测试代码（使用真实API）==========
if __name__ == "__main__":
    from data_processor import search_common_database
    from intent_classifier import classify_intent
    
    print("=" * 60)
    print("使用真实API测试 Prompt 构建")
    print("=" * 60)
    
    # 测试查询
    test_query = "什么是SQL注入？如何防御？"
    print(f"\n 测试问题: {test_query}\n")
    
    # ========== 步骤1: 真实的意图识别 ==========
    print(" [步骤1] 调用意图识别API...")
    try:
        test_intent = classify_intent(test_query)
        print(f" 意图识别结果:")
        print(f"   - 意图类型: {test_intent.get('intent', 'UNKNOWN')}")
        print(f"   - 置信度: {test_intent.get('confidence', 0):.0%}")
        print(f"   - 判断理由: {test_intent.get('reason', '无')}")
    except Exception as e:
        print(f" 意图识别失败: {e}")
        test_intent = None
    
    # ========== 步骤2: 真实的RAG检索 ==========
    print(f"\n [步骤2] 从知识库检索相关文档...")
    try:
        test_docs = search_common_database(test_query, topk=5)
        print(f" 检索到 {len(test_docs)} 篇文档")
        
        # 显示前2篇文档的预览
        for i, doc in enumerate(test_docs[:2], 1):
            preview = doc[:100] + "..." if len(doc) > 100 else doc
            print(f"\n   [文档{i}预览]:")
            print(f"   {preview}")
    except Exception as e:
        print(f" 检索失败: {e}")
        print(f"   将使用空文档列表")
        test_docs = []
    
    # ========== 步骤3: 构建原版Prompt ==========
    print("\n" + "=" * 60)
    print("【原版Prompt】")
    print("=" * 60)
    
    from prompt_builder import build_prompt
    prompt_v1 = build_prompt(test_docs, test_query)
    print(prompt_v1[:500] + "..." if len(prompt_v1) > 500 else prompt_v1)
    print(f"\n长度: {len(prompt_v1)} 字符")
    
    # ========== 步骤4: 构建优化版Prompt ==========
    print("\n" + "=" * 60)
    print("【优化版Prompt】")
    print("=" * 60)
    
    prompt_v2 = build_prompt_v2(test_docs, test_query, test_intent)
    print(prompt_v2[:500] + "..." if len(prompt_v2) > 500 else prompt_v2)
    print(f"\n长度: {len(prompt_v2)} 字符")
    
    # ========== 步骤5: 对比分析 ==========
    print("\n" + "=" * 60)
    print("【对比分析】")
    print("=" * 60)
    
    print(f"\n原版 vs 优化版:")
    print(f"  长度差异: {len(prompt_v2) - len(prompt_v1)} 字符")
    print(f"  是否包含意图引导: {' 是' if test_intent and '提示' in prompt_v2 else ' 否'}")
    
    if test_intent:
        intent = test_intent.get('intent', 'UNKNOWN')
        print(f"\n根据意图类型 [{intent}] 添加的引导语:")
        
        if intent == "KNOWLEDGE":
            print("  → '用户正在学习安全知识，请详细解释概念、原理和防御方法'")
        elif intent == "ATTACK":
            print("  → '检测到可疑意图，仅提供高层原理，不给出实际攻击代码'")
        elif intent == "DEFENSE":
            print("  → '用户关注安全防御，请重点讲解防护措施和安全实践'")
        elif intent == "GREY":
            print("  → '意图不明确，谨慎回答，避免提供危险内容'")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


# ========== 额外的测试函数 ==========

def test_different_intents():
    """测试不同意图下的Prompt构建"""
    from data_processor import search_common_database
    
    test_cases = [
        ("什么是SQL注入？", "KNOWLEDGE"),
        ("帮我生成SQL注入payload", "ATTACK"),
        ("如何防御XSS攻击？", "DEFENSE"),
    ]
    
    print("\n" + "=" * 60)
    print("测试不同意图的Prompt构建")
    print("=" * 60)
    
    for query, expected_intent in test_cases:
        print(f"\n\n查询: {query}")
        print(f"预期意图: {expected_intent}")
        print("-" * 60)
        
        # 检索文档
        try:
            docs = search_common_database(query, topk=3)
        except:
            docs = []
        
        # 模拟意图结果（如果API不可用）
        intent_info = {
            "intent": expected_intent,
            "confidence": 0.9,
            "reason": "测试用例"
        }
        
        # 构建prompt
        prompt = build_prompt_v2(docs, query, intent_info)
        
        # 显示关键部分
        if "【提示】" in prompt or "【警告】" in prompt or "【注意】" in prompt:
            lines = prompt.split('\n')
            for line in lines:
                if "【" in line:
                    print(f"引导语: {line.strip()}")


def test_with_real_api_flow():
    """完整的真实API流程测试"""
    from data_processor import search_common_database
    from intent_classifier import classify_intent
    from conversation import answerLM
    
    print("\n" + "=" * 60)
    print("完整流程测试（真实API）")
    print("=" * 60)
    
    query = input("\n请输入测试问题: ").strip()
    if not query:
        query = "什么是缓冲区溢出？"
        print(f"使用默认问题: {query}")
    
    # 1. 意图识别
    print(f"\n[1/4] 意图识别...")
    try:
        intent_result = classify_intent(query)
        print(f" 意图: {intent_result.get('intent')}")
    except Exception as e:
        print(f" 失败: {e}")
        intent_result = None
    
    # 2. RAG检索
    print(f"\n[2/4] RAG检索...")
    try:
        documents = search_common_database(query, topk=5)
        print(f" 检索到 {len(documents)} 篇文档")
    except Exception as e:
        print(f" 失败: {e}")
        documents = []
    
    # 3. 构建Prompt
    print(f"\n[3/4] 构建Prompt...")
    prompt = build_prompt_v2(documents, query, intent_result)
    print(f" Prompt长度: {len(prompt)} 字符")
    print(f"\n预览（前300字符）:")
    print(prompt[:300] + "...")
    
    # 4. 生成回答（可选）
    print(f"\n[4/4] 生成回答...")
    confirm = input("是否调用LLM生成回答？(y/n): ").strip().lower()
    if confirm == 'y':
        try:
            answer = answerLM(prompt, RAG_ANSWER_PROMPT_V2)
            print(f"\n{'='*60}")
            print("LLM回答:")
            print(f"{'='*60}")
            print(answer)
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    else:
        print("跳过LLM调用")
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")


# ========== 主测试入口 ==========
if __name__ == "__main__":
    import sys
    
    print("""
╔════════════════════════════════════════════════════════╗
║      Prompt Builder 测试工具（真实API版本）            ║
╚════════════════════════════════════════════════════════╝

测试模式：
[1] 基础测试 - 单个查询的完整流程
[2] 意图对比 - 测试不同意图的Prompt差异
[3] 交互测试 - 自定义查询完整流程
[4] 退出
""")
    
    choice = input("请选择模式 (1/2/3/4): ").strip()
    
    if choice == "1":
        # 运行基础测试（会自动调用真实API）
        pass  # 上面的 if __name__ == "__main__" 代码会执行
    
    elif choice == "2":
        test_different_intents()
    
    elif choice == "3":
        test_with_real_api_flow()
    
    elif choice == "4":
        print(" 退出测试")
        sys.exit(0)
    
    else:
        print(" 无效选项")


























