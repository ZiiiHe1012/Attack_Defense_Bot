"""
可视化前端 - Gradio实现
用于完备性评分加分项
"""

import gradio as gr
from typing import Tuple
import time

# 导入优化后的模块
try:
    from guard import validate_user_input_smart
    from intent_classifier import validate_by_intent, classify_intent, get_intent_label
    from data_processor import search_common_database
    from prompt_builder import build_prompt_v2, RAG_ANSWER_PROMPT_V2
    from conversation import answerLM
    from safety_agent import is_input_safe_v2, is_output_safe_v2
    MODULES_AVAILABLE = True
except ImportError:
    print(" 部分模块未找到，前端将使用模拟模式")
    MODULES_AVAILABLE = False


# ========== 核心处理函数 ==========

def process_query_with_details(query: str) -> Tuple[str, str]:
    """
    处理用户查询并返回详细的检测过程
    
    Returns:
        (answer, process_log): 回答和检测过程日志
    """
    process_log = []
    
    if not MODULES_AVAILABLE:
        return " 后端模块未加载，请检查依赖", "模块导入失败"
    
    # 记录开始时间
    start_time = time.time()
    
    process_log.append("###  安全检测流程\n")
    
    # ===== 第1层：智能黑名单 =====
    process_log.append("#### 1️ 智能黑名单检测")
    
    try:
        pass_blacklist, blacklist_msg = validate_user_input_smart(query)
        if not pass_blacklist:
            process_log.append(f"-  **拦截原因**: {blacklist_msg}")
            process_log.append("\n **提示**: 您的输入包含高危关键词组合。")
            return " 检测到不安全输入", "\n".join(process_log)
        
        process_log.append(f"-  {blacklist_msg}")
    except Exception as e:
        process_log.append(f"-  检测失败: {e}")
        return " 系统错误", "\n".join(process_log)
    
    # ===== 第2层：意图识别 =====
    process_log.append("\n#### 2️ 意图识别")
    
    try:
        intent_result = classify_intent(query)
        intent_label = get_intent_label(intent_result)
        process_log.append(f"- 识别结果: {intent_label}")
        process_log.append(f"- 判断理由: {intent_result.get('reason', '无')}")
        
        intent_validation = validate_by_intent(query)
        
        # 直接拦截
        if intent_validation[0] is False:
            process_log.append(f"-  **决策**: {intent_validation[1]}")
            process_log.append("\n **建议**: 您可以询问安全概念、原理或防御方法。")
            return " 检测到攻击意图", "\n".join(process_log)
        
        # 直接放行
        elif intent_validation[0] is True:
            process_log.append(f"-  **决策**: {intent_validation[1]}")
            need_ai_check = False
        
        # 灰色地带
        else:
            process_log.append(f"-  **决策**: 需要进一步AI检测")
            need_ai_check = True
    
    except Exception as e:
        process_log.append(f"-  识别失败: {e}")
        need_ai_check = True
    
    # ===== 第3层：AI安全检测（可选）=====
    if need_ai_check:
        process_log.append("\n#### 3️ AI安全检测")
        
        try:
            if not is_input_safe_v2(query):
                process_log.append("-  AI检测未通过：检测到可疑意图")
                return " AI安全检测未通过", "\n".join(process_log)
            
            process_log.append("-  通过AI安全检测")
        except Exception as e:
            process_log.append(f"-  检测失败: {e}")
    
    # ===== RAG检索 =====
    process_log.append("\n#### 4️ 知识检索")
    
    try:
        documents = search_common_database(query, 5)
        process_log.append(f"-  检索到 {len(documents)} 篇相关文档")
    except Exception as e:
        process_log.append(f"-  检索失败: {e}")
        documents = []
    
    # ===== 生成回答 =====
    process_log.append("\n#### 5️ 生成回答")
    
    try:
        intent_info = intent_result if isinstance(intent_result, dict) else None
        user_prompt = build_prompt_v2(documents, query, intent_info)
        answer = answerLM(user_prompt, RAG_ANSWER_PROMPT_V2)
        process_log.append("-  回答已生成")
    except Exception as e:
        process_log.append(f"-  生成失败: {e}")
        return " 生成回答时出错", "\n".join(process_log)
    
    # ===== 输出安全检测 =====
    process_log.append("\n#### 6️ 输出安全检测")
    
    try:
        if not is_output_safe_v2(answer, intent_result=intent_result):
            process_log.append("-  输出包含不安全内容")
            return " 输出内容检测到安全风险", "\n".join(process_log)
        
        process_log.append("-  输出安全检测通过")
    except Exception as e:
        process_log.append(f"-  检测失败: {e}")
    
    # ===== 完成 =====
    elapsed_time = time.time() - start_time
    process_log.append(f"\n **总耗时**: {elapsed_time:.2f}秒")
    process_log.append("\n---\n")
    
    return answer, "\n".join(process_log)


# ========== Gradio界面 ==========

def create_gradio_interface():
    """创建Gradio界面"""
    
    # 自定义CSS
    custom_css = """
    .container {
        max-width: 1200px;
        margin: auto;
    }
    .process-log {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 8px;
        font-size: 14px;
    }
    /* ↓↓↓ 让回答区域自动撑开 ↓↓↓ */
    .answer-md {
        max-height: none !important;
        overflow-y: visible !important;
    }
    """
    
    # 示例问题
    examples = [
        ["什么是SQL注入攻击？"],
        ["XSS攻击的原理和防御措施"],
        ["如何编写安全的登录验证代码？"],
        ["缓冲区溢出是如何发生的？"],
        ["讲解CSRF攻击及其防御方法"],
    ]
    
    # 创建界面
    with gr.Blocks(css=custom_css, title="安全知识助手") as demo:
        gr.Markdown("""
        #  安全知识助手
        
        我是一个专业的网络安全知识助手，可以帮您了解：
        - 各类网络安全漏洞的原理和特征
        - 攻击技术的工作机制
        - 防御措施和安全最佳实践
        - 安全编码规范和修复建议
        
         **注意**：我不会提供可直接用于攻击的代码或payload。
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # 输入区域
                query_input = gr.Textbox(
                    label="输入您的安全问题",
                    placeholder="例如：什么是SQL注入？如何防御？",
                    lines=3
                )
                
                # 按钮
                with gr.Row():
                    submit_btn = gr.Button(" 提交问题", variant="primary")
                    clear_btn = gr.Button(" 清空")
                
                # 示例
                gr.Examples(
                    examples=examples,
                    inputs=query_input,
                    label=" 示例问题"
                )
            
            with gr.Column(scale=1):
                # 使用说明
                gr.Markdown("""
                ###  使用说明
                
                ** 我可以回答**：
                - 安全概念和原理
                - 漏洞特征和危害
                - 防御措施和修复方法
                - 安全编码规范
                
                ** 我不会提供**：
                - 实际攻击代码
                - Payload生成
                - 绕过技巧
                - 攻击工具
                
                **示例**：
                -  "什么是SQL注入？"
                -  "如何防御XSS攻击？"
                -  "生成SQL注入payload"
                -  "给我XSS攻击脚本"
                """)
        
        # 输出区域
        gr.Markdown("---")
        
        with gr.Row():
            with gr.Column(scale=2):
                # 回答
                answer_output = gr.Markdown(
                    label=" 回答",
                    value="*您的回答将显示在这里...*",
                    elem_classes="answer-md"
                )
            
            with gr.Column(scale=1):
                # 检测过程
                process_output = gr.Markdown(
                    label=" 检测过程",
                    value="*检测日志将显示在这里...*",
                    elem_classes="process-log"
                )
        
        # 绑定事件
        def handle_submit(query):
            if not query.strip():
                return " 请输入问题", "无输入"
            
            answer, process_log = process_query_with_details(query)
            return answer, process_log
        
        submit_btn.click(
            fn=handle_submit,
            inputs=[query_input],
            outputs=[answer_output, process_output]
        )
        
        clear_btn.click(
            lambda: ("", "*您的回答将显示在这里...*", "*检测日志将显示在这里...*"),
            outputs=[query_input, answer_output, process_output]
        )
        
        # 页脚
        gr.Markdown("""
        ---
        <center>
        
         **大模型安全实践项目** |  基于多层防御机制的安全知识助手
        
        技术栈：意图识别 + 智能黑名单 + AI安全检测 + RAG
        
        </center>
        """)
    
    return demo


# ========== 启动函数 ==========

def launch_demo(share=False, server_port=7860):
    """
    启动Gradio应用
    
    Args:
        share: 是否生成公共链接
        server_port: 服务端口
    """
    if not MODULES_AVAILABLE:
        print(" 警告：后端模块未完全加载")
        print("前端将以模拟模式运行")
    
    demo = create_gradio_interface()
    
    print("\n" + "=" * 60)
    print(" 正在启动安全知识助手...")
    print("=" * 60)
    
    demo.launch(
        share=share,
        server_port=server_port,
        server_name="localhost",  # 允许外部访问
        show_error=True
    )


# ========== 主函数 ==========

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="安全知识助手 - 可视化前端")
    parser.add_argument("--share", action="store_true", help="生成公共链接")
    parser.add_argument("--port", type=int, default=7860, help="服务端口")
    
    args = parser.parse_args()
    
    launch_demo(share=args.share, server_port=args.port)


# ========== 使用说明 ==========
"""
运行方式：

1. 本地运行：
   python gradio_app.py

2. 生成公共链接（可分享）：
   python gradio_app.py --share

3. 自定义端口：
   python gradio_app.py --port 8080

界面将自动在浏览器打开，默认地址：
http://localhost:7860
"""