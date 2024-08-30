# RUC lecture monitor

This is an improved version of the previous work. The monitor mainly focus on monitoring, registering lectures from Renmin University of China (a.k.a. RUC), letting students free from the manual checking and registeration process.

Read this file in [中文](./README_zh.md).

## Installation
it is advised to create a vitual environment first.
```bash
conda create -n "spider" python=3.9 -y
conda activate spider
```
It is tested under `python==3.9`, it should also work on newer versions of python.

Then, you could install the required packages.
```bash
pip install -r requirements.txt
```

After that, you could run the monitor.

For better experiences, you could use `python GUI.py` to get a GUI interface, after setting the parameters, you are free to start your monitoring.

For programmers and geeks, a terminal version is also provided by `python main.py`.

## TODO
- [ ] Add the notification for both terminal version and GUI version.
- [ ] rewrite the GUI framework to add more diversity.
- [ ] release a binary version for windows users.


## Contributions
If you have any suggestions or ideas, please feel free to open an issue or pull request.