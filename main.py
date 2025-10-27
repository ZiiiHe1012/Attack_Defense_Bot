from flask import Flask, render_template, request, jsonify
from prompt_builder import build_prompt, RAG_ANSWER_PROMPT
from data_processor import search_common_database
from conversation import answerLM
from guard import validate_user_input, validate_prompt

app = Flask(__name__)

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            })
        
        # 用户输入安全验证
        if not validate_user_input(message):
            return jsonify({
                'success': False,
                'error': '检测到不安全的输入内容,请修改后重试。'
            })
        
        # 从知识库检索相关文档
        documents = search_common_database(message, 5)
        
        # 构建增强提示词
        user_prompt = build_prompt(documents, message)
        
        # 提示词安全验证
        if not validate_prompt(user_prompt):
            return jsonify({
                'success': False,
                'error': '检测到不安全的提示词内容,无法生成回答。'
            })
        
        # 调用大模型生成回答
        response = answerLM(user_prompt, RAG_ANSWER_PROMPT)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'系统错误: {str(e)}'
        })

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )