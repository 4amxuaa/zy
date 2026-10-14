from sdk import main  # 导入其中的函数
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

main()