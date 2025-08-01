# PepRemake
这是下载pep电子课本的项目重制版
## 使用方法
请确保你已经安装了Node.js和Python环境

先去任意一个pep官网电子书页面，打开开发者工具，查看网络请求，找到一个书籍的请求，复制cookie中的`acw_sc__v3`字段
**注：很有可能第一次看不到这个字段,这时可以尝试先跑一遍`PepDownloader.py`，然后再去浏览器pep官网电子书页面，会出现一个滑动条，你需要滑动到最右边，完成验证后，刷新页面，再次查看网络请求，就可以看到这个字段了**
然后在PepDownloader.py中设置cookie，默认是`example`，请根据实际情况设置cookie
也需要在generate.ts中设置cookie，默认是`example`，请根据实际情况设置cookie

获取书籍列表：
```
npm install
node generate.ts
```
将生成一个data.json，可以根据需要，只保留你想要下载的书。

再使用python下载书籍：
```
python -m venv .venv # 创建虚拟环境
source .venv/bin/activate  # On Windows use .venv\Scripts\activate or .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python PepDownloader.py
```
## 贡献指南
如果你想为本项目贡献代码，请遵循以下步骤：

1. Fork 本仓库
2. 创建一个新的分支
3. 在你的分支上进行修改
4. 提交你的修改并推送到远程仓库
5. 创建一个 Pull Request

更多信息请查看 [贡献指南](CONTRIBUTING.md)

我们会尽快审查你的 Pull Request。感谢您的贡献！
# 免责声明
本项目仅供学习和研究使用，所有内容均来自互联网，版权归Pep官方所有。
如有侵权，请联系删除。