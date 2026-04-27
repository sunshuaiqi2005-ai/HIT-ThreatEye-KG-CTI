from flask import Flask, render_template
from modules.kg_analysis.app import kg_bp
from modules.data_processing.app import dp_bp
import os

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# 注册图谱分析模块
app.register_blueprint(kg_bp, url_prefix='/kg_analysis')

# 注册数据处理模块
app.register_blueprint(dp_bp, url_prefix='/data_processing')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # 确保所有必要的目录存在
    os.makedirs('modules/data_processing/templates/data_processing', exist_ok=True)
    os.makedirs('modules/data_processing/static', exist_ok=True)
    
    # 设置环境变量
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'your-api-key-here'  # 请替换为您的 API 密钥
        
    app.run(debug=True, port=5000) 