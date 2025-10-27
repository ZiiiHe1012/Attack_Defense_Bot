## 2025.10.21
添加了基本的`RAG`与`Security`内容。`RAG`层面，模型可在共享数据库中进行相似文本的检索，同时拼接检索内容生成最终`prompt`；`Security`层面，模型可针对用户输入进行黑名单过滤，同时利用`AI`，使用`few-shot prompting`针对生成的最终`prompt`进行安全性检查，随后先尝试让模型给出回复，再利用`custom_prompt`进行三轮检查，最终判断输出的安全性。

## 2025.10.27
添加了前后端内容，方便用户进行使用。前端采用传统的html+css+javaScript架构，后端采用flask框架开发。

## 项目结构图
```
attack_defense_bot/                     # 项目根目录
├── README.md                           # 项目说明文档
├── requirement.txt                     # Python依赖包列表
│
├── __init__.py                         # Python包初始化文件
├── config.py                           # 配置文件
├── utils.py                            # 通用工具函数
│
├── main.py                             # 主程序入口
│   └── 功能：协调整个RAG流程
│       ├── 1. 接收用户输入
│       ├── 2. 调用 guard.validate_user_input() 进行输入验证
│       ├── 3. 调用 data_processor.search_common_database() 检索相关文档
│       ├── 4. 调用 prompt_builder.build_prompt() 构建提示词
│       ├── 5. 调用 guard.validate_prompt() 进行提示词验证
│       └── 6. 调用 conversation.answerLM() 生成最终回答
│
├── api_client.py                       # API接口封装层
│   ├── dialogue()                      # LLM对话接口
│   │   ├── 参数：user_input, custom_prompt, temperature, max_tokens
│   │   ├── 接口：POST http://10.1.0.220:9002/api/dialogue
│   │   └── 返回：模型生成的回答
│   └── search_similar_files()          # 向量数据库检索接口
│       ├── 参数：database_name, token, query, top_k, metric_type等
│       ├── 接口：POST http://10.1.0.220:9002/api/databases/{database_name}/search
│       └── 返回：相似度最高的top_k个文档
│
├── guard.py                            # 安全检测模块（统一入口）
│   ├── validate_user_input()           # 用户输入安全验证
│   │   ├── 调用 blacklist.get_blacklist() 获取黑名单
│   │   └── 检查输入是否包含恶意关键词
│   └── validate_prompt()               # 提示词安全验证
│       ├── 调用 safety_agent.is_input_safe() 检测输入安全性
│       └── 调用 safety_agent.is_output_safe() 检测输出安全性
│
├── blacklist.py                        # 黑名单配置模块
│   ├── Blacklist类                     # 黑名单规则定义
│   │   ├── INSTRUCTION_OVERRIDE        # 指令覆盖攻击关键词
│   │   ├── ROLE_CONFUSION              # 角色混淆攻击关键词
│   │   ├── INFORMATION_LEAK            # 信息泄露攻击关键词
│   │   ├── JAILBREAK                   # 越狱攻击关键词
│   │   ├── CODE_INJECTION              # 代码注入攻击模式
│   │   └── SOCIAL_ENGINEERING          # 社会工程攻击关键词
│   └── get_blacklist()                 # 获取完整黑名单字典
│
├── safety_agent.py                     # AI驱动的安全检测模块
│   ├── INPUT_CHECKING_PROMPT           # 输入检测的系统提示词
│   ├── OUTPUT_CHECKING_PROMPT          # 输出检测的系统提示词
│   ├── is_input_safe()                 # 使用LLM判断输入是否安全
│   │   ├── 调用 api_client.dialogue() 
│   │   └── 返回 true/false
│   └── is_output_safe()                # 使用LLM判断输出是否包含攻击内容
│       ├── 先调用 dialogue() 生成输出
│       ├── 再调用3次 dialogue() 检测输出安全性
│       └── 返回 true/false
│
├── data_processor.py                   # 数据处理模块
│   └── search_common_database()        # 从通用知识库检索文档
│       ├── 调用 api_client.search_similar_files()
│       ├── 参数：查询文本q, 返回数量topk
│       └── 返回：文档文本列表
│
├── prompt_builder.py                   # 提示词构建模块
│   ├── RAG_ANSWER_PROMPT               # RAG系统提示词常量
│   │   └── 定义：助手角色、任务目标、回答要求
│   └── build_prompt()                  # 构建完整的用户提示词
│       ├── 参数：检索到的文档列表, 用户查询
│       └── 返回：格式化的提示词字符串
│
└── conversation.py                     # 对话管理模块
    └── answerLM()                      # 调用LLM生成回答
        ├── 参数：user_prompt（用户提示词）, system_prompt（系统提示词）
        ├── 调用 api_client.dialogue()
        └── 返回：模型回答文本

═══════════════════════════════════════════════════════════════

【模块依赖关系图】

main.py (主流程)
    ├──> guard.py (安全检测)
    │       ├──> blacklist.py (关键词黑名单)
    │       └──> safety_agent.py (AI安全检测)
    │               └──> api_client.py (调用LLM判断)
    ├──> data_processor.py (文档检索)
    │       └──> api_client.py (调用向量数据库)
    ├──> prompt_builder.py (提示词构建)
    └──> conversation.py (生成回答)
            └──> api_client.py (调用LLM对话)

api_client.py (底层服务)
    ├──> 外部LLM服务 (10.1.0.220:9002/api/dialogue)
    └──> 外部向量数据库 (10.1.0.220:9002/api/databases/*/search)

═══════════════════════════════════════════════════════════════

【执行流程】

用户输入 
    ↓
[步骤1] guard.validate_user_input() - 黑名单过滤
    ↓
[步骤2] data_processor.search_common_database() - 检索相关文档
    ↓
[步骤3] prompt_builder.build_prompt() - 组装提示词
    ↓
[步骤4] guard.validate_prompt() - AI安全检测（输入+输出）
    ↓
[步骤5] conversation.answerLM() - 生成最终回答
    ↓
输出结果
```