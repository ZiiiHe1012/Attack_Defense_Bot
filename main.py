from flask import Flask, render_template, request, jsonify
from prompt_builder import build_prompt, RAG_ANSWER_PROMPT_V2
from data_processor import search_common_database, advanced_search, search_database_bilingual
from conversation import answerLM
from intent_classifier import classify_intent_v2, validate_by_intent_v2
from safety_response import generate_safe_response
from attack_pattern_detector import AttackPatternDetector
from safety_agent import is_input_safe, is_output_safe
from context_intent import context_intent_validation, ConversationManager

app = Flask(__name__)
conversation_manager = ConversationManager(max_turns=5)

def process_query_no_blacklist(q: str) -> dict:
    """
    五层安全检测流程
    
    1. 移除误拦截严重的黑名单机制
    2. 依靠多层智能检测保证安全性
    3. 每层都有上下文理解能力
    4. 拦截时提供教育性回复
    
    Args:
        q: 用户问题
    Returns:
        {
            "success": bool,
            "answer": str,
            "error": str,
            "logs": [{"step": str, "status": str, "message": str}],
            "blocked": bool
        }
    """
    result = {
        "success": False,
        "answer": "",
        "error": "",
        "logs": [],
        "blocked": False
    }
    
    # === 第1层: 意图识别 ===
    result["logs"].append({
        "step": "意图识别", 
        "status": "processing", 
        "message": "分析用户意图中..."
    })
    
    intent_result = classify_intent_v2(q)
    intent = intent_result.get("intent", "GREY")
    confidence = intent_result.get("confidence", 0.5)
    
    # === 第2层: 上下文检测 ===
    result["logs"].append({
        "step": "上下文检测", 
        "status": "processing", 
        "message": "检查对话历史..."
    })
    
    is_context_safe, context_reason, _ = context_intent_validation(
        q, 
        conversation_manager.get_history()
    )
    
    if is_context_safe is False:
        result["logs"].append({
            "step": "上下文检测", 
            "status": "fail", 
            "message": context_reason
        })
        result["blocked"] = True
        result["answer"] = generate_safe_response(intent_result, q)
        result["success"] = True
        return result
    
    result["logs"].append({
        "step": "上下文检测", 
        "status": "success", 
        "message": context_reason
    })
    
    # === 第3层: 本次意图验证 ===
    intent_validation = validate_by_intent_v2(q)
    
    # 情况1: 明确的知识学习或防御实践 - 直接放行
    if intent_validation[0] is True:
        result["logs"].append({
            "step": "意图识别", 
            "status": "success", 
            "message": intent_validation[1]
        })
        need_pattern_check = False
        need_ai_check = False
        
    # 情况2: 明确的攻击意图 - 直接拦截并教育
    elif intent_validation[0] is False:
        result["logs"].append({
            "step": "意图识别", 
            "status": "fail", 
            "message": intent_validation[1]
        })
        result["blocked"] = True
        result["answer"] = generate_safe_response(intent_result, q)
        result["success"] = True
        return result
        
    # 情况3: 灰色地带 - 需要进一步检测
    else:
        intent_label = (
            f"{intent} "
            f"(置信度: {confidence:.0%}, "
            f"风险: {intent_result.get('risk_level', 'medium')})"
        )
        result["logs"].append({
            "step": "意图识别", 
            "status": "warning", 
            "message": intent_label
        })
        need_pattern_check = True
        need_ai_check = True
    
    # === 第4层: 攻击模式检测(仅灰色地带) ===
    if need_pattern_check:
        result["logs"].append({
            "step": "模式检测", 
            "status": "processing", 
            "message": "检测攻击特征模式..."
        })
        
        should_block, block_reason = AttackPatternDetector.should_block(
            q, 
            intent_result
        )
        
        if should_block:
            result["logs"].append({
                "step": "模式检测", 
                "status": "fail", 
                "message": block_reason
            })
            result["blocked"] = True
            result["answer"] = generate_safe_response(intent_result, q)
            result["success"] = True
            return result
        else:
            result["logs"].append({
                "step": "模式检测", 
                "status": "success", 
                "message": "未检测到明显攻击模式"
            })
    
    # === 第5层: AI安全检测(双重不确定) ===
    if need_ai_check:
        result["logs"].append({
            "step": "AI安全检测", 
            "status": "processing", 
            "message": "深度语义分析中..."
        })
        
        if not is_input_safe(q):
            result["logs"].append({
                "step": "AI安全检测", 
                "status": "fail", 
                "message": "AI检测到潜在安全风险"
            })
            result["blocked"] = True
            result["answer"] = generate_safe_response(intent_result, q)
            result["success"] = True
            return result
            
        result["logs"].append({
            "step": "AI安全检测", 
            "status": "success", 
            "message": "通过AI安全检测"
        })
    
    # === 第6层: RAG检索 ===
    result["logs"].append({
        "step": "RAG检索", 
        "status": "processing", 
        "message": "检索相关知识..."
    })
    
    try:
        supplement = advanced_search(q, 'decomposed')
        L1_documents = search_database_bilingual(q, 5)
        
        doc_count = len(L1_documents) + (len(supplement) if supplement else 0)
        result["logs"].append({
            "step": "RAG检索", 
            "status": "success", 
            "message": f"检索到 {doc_count} 个相关文档"
        })
    except Exception as e:
        result["logs"].append({
            "step": "RAG检索", 
            "status": "warning", 
            "message": f"检索失败: {str(e)}"
        })
        supplement = None
        L1_documents = []
    
    # 构建增强提示词
    user_prompt = build_prompt(L1_documents, q, intent_result, supplement)
    
    # === 第7层: 生成回答 ===
    result["logs"].append({
        "step": "生成回答", 
        "status": "processing", 
        "message": "AI生成回答中..."
    })
    
    try:
        answer = answerLM(user_prompt, RAG_ANSWER_PROMPT_V2, max_tokens=4096)
        result["logs"].append({
            "step": "生成回答", 
            "status": "success", 
            "message": "回答生成完成"
        })
    except Exception as e:
        result["logs"].append({
            "step": "生成回答", 
            "status": "fail", 
            "message": str(e)
        })
        result["error"] = f"生成失败: {e}"
        return result
    
    # === 第8层: 输出安全检测 ===
    result["logs"].append({
        "step": "输出检测", 
        "status": "processing", 
        "message": "检测输出安全性..."
    })
    
    if not is_output_safe(answer, intent_result=intent_result):
        result["logs"].append({
            "step": "输出检测", 
            "status": "fail", 
            "message": "输出包含不安全内容"
        })
        result["blocked"] = True
        result["answer"] = generate_safe_response(intent_result, q)
        result["success"] = True
        return result
        
    result["logs"].append({
        "step": "输出检测", 
        "status": "success", 
        "message": "输出内容安全"
    })
    
    # === 成功返回 ===
    result["success"] = True
    result["answer"] = answer
    
    # 记录对话历史
    conversation_manager.add_turn(q, answer)
    
    return result


@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')


@app.route('/clear_history', methods=['POST'])
def clear_history():
    """清除对话历史"""
    conversation_manager.clear()
    return jsonify({"success": True, "message": "对话历史已清除"})


@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        # 基础验证
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空',
                'logs': []
            })
        
        # 长度限制
        if len(message) > 2000:
            return jsonify({
                'success': False,
                'error': '输入过长,请控制在2000字符以内',
                'logs': []
            })
        
        # 调用核心处理函数
        result = process_query_no_blacklist(message)
        return jsonify(result)
        
    except Exception as e:
        print(f"系统错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'系统错误: {str(e)}',
            'logs': []
        })


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '请求的资源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    print("""

   安全知识助手 - Web服务启动中...                     

   访问地址: http://127.0.0.1:5000                               

    """)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    )