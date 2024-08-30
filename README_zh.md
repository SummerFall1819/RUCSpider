# RUC 讲座监听器

这是基于之前工作的一个改进版本。监听器侧重于监控与报名中国人民大学的讲座，让诸同学无需手动检查与报名。

使用 [English](./README.md) 阅读此文章。

## 安装
推荐创建一个虚拟环境。
```bash
conda create -n "spider" python=3.9 -y
conda activate spider
```
该项目在 `python==3.9` 的环境下可以运行, 其应当也能在更高版本的 `python` 上运行.

之后，下载依赖文件
```bash
pip install -r requirements.txt
```

操作完成后，就可以监听讲座了。

为了更好的体验，可以通过 `python GUI.py` 命令打开 GUI 窗口，在设置完毕参数后，就可以开始监听了。

对于程序员而言，终端版本也可以通过 `python main.py` 命令运行。

## 待做
- [ ] 为终端版本和 GUI 版本添加通知。
- [ ] 重写 GUI 框架，增加更多样性。

## 贡献
如果你有任何建议或想法，请随时开 issue 或 pull request。
