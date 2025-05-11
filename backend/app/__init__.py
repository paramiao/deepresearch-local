from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # 启用跨域资源共享
    
    # 导入路由
    from app.routes import chat_routes, research_routes
    app.register_blueprint(chat_routes.bp)
    app.register_blueprint(research_routes.bp)
    
    # 添加API状态检查端点
    @app.route('/api/status', methods=['GET'])
    def check_status():
        return jsonify({"status": "ok", "message": "API服务正常运行"})
    
    return app
