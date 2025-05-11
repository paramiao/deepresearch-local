import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 使用端口8000，避免与系统其他服务冲突
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
