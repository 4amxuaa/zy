# from sdk import main  # 导入其中的函数
# import os
# base_dir = os.path.dirname(os.path.abspath(__file__))
# os.chdir(base_dir)

# main()


from flask import Flask, render_template_string

app = Flask(__name__)

index = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>首页</title>
</head>
<body>
    <h1>欢迎来到 Flask！</h1>
    <p>这是我的主页。</p>
</body>
</html>
"""

@app.route('/')
def home():
    return index

if __name__ == '__main__':
    app.run(debug=True)