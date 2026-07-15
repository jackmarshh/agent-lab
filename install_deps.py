import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", package])

if __name__ == "__main__":
    try:
        print("开始安装 chromadb...")
        install("chromadb")
        print("开始安装 sentence-transformers...")
        install("sentence-transformers")
        print("✅ 安装完成！")
    except Exception as e:
        print(f"❌ 安装失败: {e}")
