from typing import Dict
# set a basic notifier, it will be used to send notifications.

from pydantic import BaseModel


'''
args 要求:
1. 无需实例化，就可以获得所有的参数名称和类型 （input ，或者继承自一个基类）
2. 通过 update 可以更新参数，并自动检查     
3. 在参数齐全之后可以 export 参数为 dict 形式。
'''

# class ArgValidation(BaseModel):
#     '''
#     Yes, it is meant to avoid the need of instantiation.
#     '''
#     pass

PYDANTIC_TEMPLATE = """
class ArgValidation(BaseModel):
{content}
"""

class NotifierArgs(object):
    
    def __init__(self, attrs:Dict[str,str]):
        
        self.attrs = attrs
        empty_attr = {k:None for k in self.attrs.keys()}
        self.__dict__.update(empty_attr)
        
        
    def get_arg_names(self):
        return list(self.attrs.keys())
    
    def get_all_args(self):
        params = { k: v for k,v in self.__dict__.items() if k in self.attrs.keys()}
        
        def dict2pydantic(attrs:dict):
            codes = ""
            for k,v in attrs.items():
                codes += f"    {k}: {v}\n"
            return codes
        
        validate_class = PYDANTIC_TEMPLATE.format(content=dict2pydantic(self.attrs))
        
        print(validate_class)
        
        exec(validate_class)
        
        print(params)
        
        validator = ArgValidation.model_validate(params)
        print(validator.model_dump())
        return validator.model_dump()

# args = NotifierArgs({"app_token":"str","UID":"str"})

# args.app_token = "123"
# args.UID = "456"

# print('>',args.get_all_args())



def dict2pydantic(attrs:dict):
    codes = ""
    for k,v in attrs.items():
        codes += f"    {k}: {v}\n"
    return codes




d = {
    "name":"str",
    "age":"int"
}


        

tt = dict2pydantic(d)

exec(PYDANTIC_TEMPLATE.format(content=tt))

dd = {
    'name': 'a',
    'age': 1
}

y = ArgValidation.model_validate(dd)
print(y.model_dump())







# class BasicNotifier(object):
    
#     def __init__(self):
#         self.args: NotifierArgs = None
    
#     def get_args(self):
        