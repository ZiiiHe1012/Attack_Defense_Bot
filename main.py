from flask import Flask, render_template, request, jsonify
from prompt_builder import build_prompt, RAG_ANSWER_PROMPT, RAG_ADVANCED_ANSWER_PROMPT, build_prompt, RAG_ANSWER_PROMPT_V2
from data_processor import search_common_database, advanced_search,search_database_bilingual
from conversation import answerLM
from guard import validate_user_input, validate_prompt
from intent_classifier import validate_by_intent, get_intent_label, classify_intent
from safety_agent import is_input_safe, is_output_safe
from context_intent import context_intent_validation, ConversationManager

app = Flask(__name__)
conversation_manager = ConversationManager(max_turns=5)

def process_query(q: str) -> dict:
    """
    六层安全检测流程
    Args:
        q: 用户问题
    Returns:
        {
            "success": bool,
            "answer": str,
            "error": str,
            "logs": [{"step": str, "status": str, "message": str}]
        }
    """
    result = {
        "success": False,
        "answer": "",
        "error": "",
        "logs": []
    }

    # 第1层：黑名单
    result["logs"].append({"step": "黑名单", "status": "processing", "message": "检测中..."})
    pass_blacklist, blacklist_msg = validate_user_input(q)
    if not pass_blacklist:
        result["logs"].append({"step": "黑名单", "status": "fail", "message": blacklist_msg})
        result["error"] = f"检测到不安全输入: {blacklist_msg}"
        return result
    result["logs"].append({"step": "黑名单", "status": "success", "message": blacklist_msg})
    
    # 第2层：意图识别
    result["logs"].append({"step": "意图识别", "status": "processing", "message": "识别中..."})
    # 先获取完整的意图信息（用于后续输出检测）
    intent_result = classify_intent(q)
    # 进行上下文意图验证
    result["logs"].append({"step": "上下文检测", "status": "processing", "message": "检查中..."})
    is_safe, reason, _ = context_intent_validation(q, conversation_manager.get_history())
    if is_safe is False:
        result["logs"].append({"step": "上下文检测", "status": "fail", "message": reason})
        result["error"] = reason
        return result
    result["logs"].append({"step": "上下文检测", "status": "success", "message": reason})
    # 再进行本次意图验证（决定是否放行/拦截/进入AI检测）
    intent_validation = validate_by_intent(q)
    # 直接放行
    if intent_validation[0] is True:
        result["logs"].append({"step": "意图识别", "status": "success", "message": intent_validation[1]})
        need_ai_check = False
    # 直接拦截
    elif intent_validation[0] is False:
        result["logs"].append({"step": "意图识别", "status": "fail", "message": intent_validation[1]})
        result["error"] = intent_validation[1] + "\n\n建议：您可以询问漏洞原理、防御措施等教育性内容。"
        return result
    # 灰色地带
    else:
        result["logs"].append({"step": "意图识别", "status": "warning", "message": get_intent_label(intent_result)})
        need_ai_check = True
    
    # 第3层：AI安全检测（灰色地带）
    if need_ai_check:
        result["logs"].append({"step": "AI安全检测", "status": "processing", "message": "检测中..."})
        if not is_input_safe(q):
            result["logs"].append({"step": "AI安全检测", "status": "fail", "message": "检测到可疑意图"})
            result["error"] = "AI安全检测未通过：检测到可疑意图"
            return result
        result["logs"].append({"step": "AI安全检测", "status": "success", "message": "通过检测"})
    
    # 第4层：RAG检索
    result["logs"].append({"step": "RAG检索", "status": "processing", "message": "检索中..."})
    try:
        # Advanced Rag pipeline, integrated into one entry function
        # decomposed - 问题分解 recursive - 叠代检索
        supplement = advanced_search(q, 'decomposed')
        # 从知识库检索相关文档
        L1_documents = search_database_bilingual(q, 5)
        result["logs"].append({"step": "RAG检索", "status": "success", "message": f"检索到相关文档"})
    except Exception as e:
        result["logs"].append({"step": "RAG检索", "status": "warning", "message": f"检索失败: {e}"})
        #Advanced Rag pipeline, integrated into one entry function
        # 构建增强提示词
    user_prompt = build_prompt(L1_documents, q, intent_result, supplement)
    
    # 第5层：生成回答
    result["logs"].append({"step": "生成回答", "status": "processing", "message": "生成中..."})
    try:
        answer = answerLM(user_prompt, RAG_ANSWER_PROMPT_V2, max_tokens=4096)
        result["logs"].append({"step": "生成回答", "status": "success", "message": "已生成"})
    except Exception as e:
        result["logs"].append({"step": "生成回答", "status": "fail", "message": str(e)})
        result["error"] = f"生成失败: {e}"
        return result
    
    # 第6层：输出安全检测
    result["logs"].append({"step": "输出检测", "status": "processing", "message": "检测中..."})
    if not is_output_safe(answer, intent_result=intent_result):
        result["logs"].append({"step": "输出检测", "status": "fail", "message": "输出包含不安全内容"})
        result["error"] = "输出内容检测到安全风险"
        return result
    result["logs"].append({"step": "输出检测", "status": "success", "message": "输出安全"})
    
    # 成功返回
    result["success"] = True
    result["answer"] = answer
    # 记录对话
    conversation_manager.add_turn(q, answer)

    return result

@app.route('/')
def index():
    # 渲染主页
    return render_template('index.html')

@app.route('/clear_history', methods=['POST'])
def clear_history():
    # 清除对话历史
    conversation_manager.clear()
    return jsonify({"success": True})

@app.route('/chat', methods=['POST'])
def chat():
    # 处理聊天请求
    try:
        data = request.json
        message = data.get('message', '')
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空',
                'logs': []
            })
        # 用户输入安全验证
        if not validate_user_input(message):
            return jsonify({
                'success': False,
                'error': '检测到不安全的输入内容,请修改后重试。'
            })
        # 调用核心处理函数
        result = process_query(message)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'系统错误: {str(e)}',
            'logs': []
        })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '请求的资源不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

# 启动应用
if __name__ == '__main__':
    print("""安全知识助手 - Web服务启动中...""")
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )