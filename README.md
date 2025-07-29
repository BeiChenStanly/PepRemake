# PepRemake
这是下载pep电子课本的项目重制版
## 使用方法
请确保你已经安装了Node.js和Python环境
先获取书籍列表：
```
npm install
node generate.ts
```
将生成一个data.json，可以根据需要，只保留你想要的  
再去任意一个pep官网面，打开开发者工具，查看网络请求，找到一个书籍的请求，复制cookie
然后在PepDownloader.py中设置cookie，默认是`688856b50fd4f016824d8e516aeef39531cc5e94`，请根据实际情况设置cookie
再使用python下载书籍：
```
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate or .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python PepDownloader.py
```
如有侵权，请联系删除