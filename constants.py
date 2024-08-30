import sys
from typing import List, Dict, Callable, Literal, NewType

Methods = Literal['Void','Toaster','WxPusher']

from loguru import logger

from windows_toasts import Toast, WindowsToaster
from windows_toasts.wrappers import ToastDisplayImage

LOGGER_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> ' \
            '| <cyan>{name}</cyan>:<cyan>{function: >20}</cyan>:<yellow>{line: >4}</yellow> - <level>{message}</level>'
            
logger.remove(0)

SELECTORS = {
    "不限": {
        "不限": ["不限"]
    },
    "素质拓展认证": {
        "不限": ["不限"],
        "形势与政策": ["不限", "形势与政策研讨", "形势与政策讲座"],
        "学术科研类": ["不限", "学术科研类"],
        "学业辅导类": ["不限", "学业辅导类", "学风建设"],
        "课外阅读类": ["不限", "课外阅读类", "读史读经典"],
        "实践调查类": ["不限"],
        "公益服务类": ["不限"],
        "活动组织类": ["不限"],
        "体育锻炼类": ["不限"],
        "国际交流类": ["不限"],
        "文化艺术类": ["不限"],
        "创业旅游类": ["不限"]
    },
    "我和我的祖国": {
        "不限": ["不限"],
        "理想信念模块": ["不限"],
        "精神传承模块": ["不限"],
        "纪念庆祝模块": ["不限"],
        "学习学术模块": ["不限"],
        "体育锻炼模块": ["不限"],
        "实践调研模块": ["不限"],
        "奉献公益模块": ["不限"],
        "创新创意模块": ["不限"],
        "文化艺术模块": ["不限"],
        "宣传展示模块": ["不限"]
    },
    "读史读经典": {
        "不限": ["不限"]
    },
    "新生入学教育": {
        "不限": ["不限"],
        "本科新生入学教育": ["不限"],
        "研究生新生入学教育": ["不限"]
    },
    "辅导员能力提升": {
        "不限": ["不限"]
    },
    "军训": {
        "不限": ["不限"],
        "国防及安全教育": ["不限"],
        "军事技能理论教育": ["不限"],
        "党史校史学习": ["不限"],
        "体能训练": ["不限"],
        "科目实训": ["不限"]
    },
    '"通识讲座"活动': {
        "不限": ["不限"],
        "人文社会科学类": [
            "不限",
            "哲学与伦理",
            "历史与文化",
            "思辨与表达",
            "审美与诠释",
            "世界与中国",
            "习近平新时代中国特色社会主义思想系列"
            ],
    "自然科学类": ["不限", "科学与技术", "实证与推理", "生命与环境"]
    },
    '"进学蓄德"读书活动': {
        "不限": ["不限"]
    }
}


ALIAS:Dict[str,int] = {
    "不限":0,
    "":0,
    "素质拓展认证":95,
    "我和我的祖国":96,
    "读史读经典":109,
    "新生入学教育":112,
    "辅导员能力提升":117,
    "军训":120,
    "\"通识讲座\"活动":132,
    "\"进学蓄德\"读书活动":144,

    "形势与政策":22,
    "学术科研类":25,
    "学业辅导类":27,
    "课外阅读类":29,
    "实践调查类":31,
    "公益服务类":33,
    "活动组织类":35,
    "体育锻炼类":37,
    "国际交流类":39,
    "文化艺术类":41,
    "就业创业类":43,

    "理想信念模块":97,
    "精神传承模块":98,
    "纪念庆祝模块":99,
    "学习学术模块":100,
    "体育锻炼模块":101,
    "实践调研模块":102,
    "奉献公益模块":103,
    "创新创意模块":104,
    "文化艺术模块":105,
    "宣传展示模块":106,

    "本科新生入学教育":113,
    "研究生新生入学教育":115,

    "国防及安全教育":121,
    "军事技能理论教育":122,
    "党史校史学习":123,
    "体能训练":124,
    "科目实训":125,

    "人文社会科学类":133,
    "自然科学类":134,

    "阅读计划":145,

    "形势与政策研讨":24,
    "形势与政策讲座":108,
    "原活动":148,

    "哲学与伦理":135,
    "历史与文化":136,
    "思辨与表达":137,
    "审美与诠释":138,
    "世界与中国":139,
    "习近平新时代中国特色社会主义思想系列":143,
    "科学与技术":140,
    "实证与推理":141,
    "生命与环境":142
}

def toast_notifier(lectures:List[Dict]):
    toast_content = '\n'.join([f'Lecture {lec["aid"]} succesfully registered' for lec in lectures])
    toast_content += '\nClick to open website for first lecture.'
    toaster = WindowsToaster('RUC Lecture Notifier')
    newToast = Toast()
    newToast.text_fields = [toast_content]
    newToast.AddImage(ToastDisplayImage.fromPath('./RUCWeb.ico'))
    newToast.launch_action = 'https://v.ruc.edu.cn//campus#/activity/partakedetail/{aid}/description'.format(aid = lectures[0]['aid'])
    toaster.show_toast(newToast)


NOTIFIER:Dict[str,Callable] = {
    'none': lambda lectures: None,
    'toast': toast_notifier
}


DEFAULT_LECTURE = ["素质拓展认证","形势与政策","形势与政策讲座"]




