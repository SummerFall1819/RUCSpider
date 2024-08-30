
import os
import re
import sys
import json
import base64
import pickle
import atexit
from typing import Literal, Dict, Any, Union, List, Callable, Set, Tuple

import requests
import schedule
from loguru import logger
from fake_useragent import UserAgent
from datetime import datetime, timedelta

from tenacity import retry, stop_after_attempt, wait_fixed,retry_if_exception

from constants import ALIAS, LOGGER_FORMAT, NOTIFIER
from constants import SELECTORS
from constants import Methods

COOKIE_VALID_TIME = 18000

logger.remove(handler_id = None)

logger.add(sys.stderr, 
            format    = LOGGER_FORMAT,
            diagnose  = True,
            backtrace = True)

@logger.catch
@retry(stop = stop_after_attempt(3), 
        wait = wait_fixed(1), 
        retry_error_callback = lambda rs: print(rs.outcome.result()),
        retry = retry_if_exception(requests.exceptions.RequestException),
        reraise = True)
def query_html(method        : Literal['GET', 'POST']            = 'GET',
                output_format: Literal['text','json','response'] = 'json',
                encoding     : str                               = 'utf-8',
                **kwargs) -> Union [str , Dict[str,str], requests.Response]: 
    """
    This function is used as the base function to query the html.

    Args:
        method (Literal[GET|POST], optional): The method of the server. Defaults to 'GET'.
        is_json (bool, optional): the expected result is a json or not. Defaults to True.
        vervose (bool, optional): whether to output some middle information. Defaults to False.
        encoding (str, optional): The encoding of the website. Defaults to 'utf-8'.
        
        **kwargs: The parameters of the request. use this as origin requests function.
        
    Returns:
        str | Dict[str,str]: The result of the request.
        if is_json is set as true, then returns a dict, else returns a str.
        
    >>> query_html('GET', 'text', url='https://www.baidu.com', headers = headers)
    """
    
    if method == 'GET':
        response:requests.Response = requests.get(**kwargs)
    elif method == 'POST':
        response:requests.Response = requests.post(**kwargs)
    else:
        raise ValueError(f"method {method} is not supported")
    
    response.encoding = encoding
    
    if output_format == 'json':
        return response.json()
    elif output_format == 'text':
        return response.text
    elif output_format == 'response':
        return response
    else:
        raise ValueError(f"output_format {output_format} is not supported")

class Maintainer(object):
    def __init__(self, hold_second: int): 
        self.content = None
        self.set_content = False
        self.hold_second = hold_second
        self.birth_time = datetime.now()
        
    def __repr__(self) -> str:
        return f'{self.content} with {self.hold_second} seconds'
        return f'Maintainer {self.content} with type {type(self.content)}, Birth Time {self.birth_time}, Expire: {self.is_expired()}'
    
    def __str__(self):
        return f'{self.content} with {self.hold_second} seconds'
    
    def __eq__(self, other) -> bool:
        if type(other) == type(self.content):
            return self.content == other
        elif type(other) == type(self):
            return self.content == other.content
        else:
            return False
    
    def __hash__(self):
        return hash(self.content)
        
    def is_expired(self) -> bool:
        if self.set_content == False:
            return True
        else:
            return datetime.now() - self.birth_time > timedelta(seconds = self.hold_second)
    
    def update_content(self, content:Any):
        '''
        The content is at least str()
        '''
        self.set_content = True
        self.content:Any = content
        self.birth_time = datetime.now()
    
    @logger.catch
    def get_content(self, force_get:bool = False):
        # assert self.set_content or force_get, "Maintainer has no content"
        if self.set_content == False:
            return None
        if self.is_expired() and not force_get:
            return None
        else:
            return self.content
    
class SelectorManager(object):
    def __init__(self):
        self.source_selector:Dict[str:Dict[str,List[str]]] = SELECTORS
        self.mappings:Dict[str,int] = ALIAS
        
    def get_childrens(self, selectors:List[str] = None) -> List[str]:
        """
        This function is mainly used for combo box, changing the sub-level by previous fathers.

        _extended_summary_

        Args:
            selectors (List[str], optional): The very category it leads. Defaults to None.

        Returns:
            List[str]: _description_
        """
        if selectors is None:
            selectors = []
        
        if len(selectors) >= 3:
            return []
            
        result = self.source_selector
        
        for types in selectors:
            if result == {}:
                return []
            result = result.get(types, {})
            
        if isinstance(result, dict):
            return list(result.keys())
        elif isinstance(result, list):
            return result
        else:
            return []
        
    def get_mapping(self, selectors:List[str] = None) -> List[int]:
        """
        get the selectors as ints that indicates the selectors.

        _extended_summary_

        Args:
            selectors (List[str], optional): _description_. Defaults to None.

        Returns:
            List[int]: The number which the server uses.
        """
        
        if selectors is None:
            selectors = []
        
        if len(selectors) > 3:
            return [0,0,0]
        
        mappings = [self.mappings.get(types, 0) for types in selectors]
        
        if len(mappings) < 3:
            mappings += [0] * (3 - len(mappings))
        
        # Check for validness.
        if mappings[1] == 0:
            mappings = [mappings[0],0,0]
        
        if mappings[0] == 0:
            mappings = [0,0,0]
            
        return mappings

class RUCSpider(object):
    '''
    This class is responsible for interact with ruc server. which includes:
    
    1. login.
        1) detect captcha.
        2) login in with the captcha.
    2. maintain the cookie so the server is always accessble.
    '''
    
    def __init__(self, load_path:str = './spider.pkl'): 
        
        if load_path != None and os.path.exists(load_path):
            try:
                with open(load_path, 'rb') as f:
                    oldspider:RUCSpider = pickle.load(f)
                    self.user_id = oldspider.user_id
                    self.passward = oldspider.passward
                    self.token = oldspider.token
                    self.captcha = oldspider.captcha
                    self.captcha_id = oldspider.captcha_id
                    self.lecture_pool_checked = oldspider.lecture_pool_checked
                    self.mapping = oldspider.mapping
                    self.cookie_maintainer = oldspider.cookie_maintainer
                    self.ua = oldspider.ua
                    self.save_path = load_path
                    self.running = False
                    self.locking = False
                    
                    print(self.captcha, self.captcha_id)
                    
                logger.success("Success load previous spider instance.")
                return
            except:
                logger.error("Fail to load previous spider instance. Initializing a new one.")
        
        self.user_id   : str = ''
        self.passward  : str = ''
        self.token     : str = ''
        self.captcha   : str = ''
        self.captcha_id: str = ''
        
        self.running:bool = False
        
        self.save_path = load_path
        
        self.ua = UserAgent()
        self.cookie_maintainer:Maintainer = Maintainer(COOKIE_VALID_TIME)
        
        self.lecture_pool_checked:Set[Maintainer] = set()
        self.mapping:Dict[str:int] = ALIAS
        self.locking:bool = False
        
        self.notify_method: Methods = 'Void'
        
    def __repr__(self) -> str:
        return 'Spider'
    
    def __getstate__(self) -> object:
        
        information = {'user_id': self.user_id, 
                        'passward': self.passward, 
                        'token': self.token, 
                        'captcha': self.captcha, 
                        'captcha_id': self.captcha_id, 
                        'lecture_pool_checked': self.lecture_pool_checked, 
                        'mapping': self.mapping, 
                        'cookie_maintainer': self.cookie_maintainer}
        
        return information
    
    def __setstate__(self, state:object) -> None:

        self.user_id   = state['user_id']
        self.passward  = state['passward']
        self.token     = state['token']
        self.captcha   = state['captcha']
        self.captcha_id= state['captcha_id']
        self.lecture_pool_checked = state['lecture_pool_checked']
        self.mapping   = state['mapping']
        self.cookie_maintainer = state['cookie_maintainer']

        self.ua = UserAgent()
        
    def get_token(self):
        """
        Get the tokens, which is used to login.
        """
        
        token_url = r"https://v.ruc.edu.cn/auth/login?&proxy=true&redirect_uri=https://v.ruc.edu.cn/oauth2/authorize?client_id=accounts.tiup.cn&redirect_uri=https://v.ruc.edu.cn/sso/callback?school_code=ruc&theme=schools&response_type=code&school_code=ruc&scope=all&state=jnTBbsfBumjuSrfZ&theme=schools&school_code=ruc"
        
        headers = {'user-Agent': self.ua.random}
        
        html_with_token:str = query_html(method = 'GET', 
                                    output_format = 'text',
                                    url     = token_url, 
                                    headers = headers)
        
        token_regex = re.compile(r'(?<=<input type="hidden" name="csrftoken" value=")([\S]+)(?=" id="csrftoken" \/>)')
        
        self.token = re.search(token_regex, html_with_token)[0]
        
        
    def get_captcha(self, manual = False):
        
        logger.info("Retrieving and recognize captcha")
        
        captcha_url = r"https://v.ruc.edu.cn/auth/captcha"
        headers = {'user-Agent': self.ua.random}
        
        captcha_json:Dict = query_html(url  = captcha_url,
                                    headers = headers)
        
        b64_regex = re.compile(r"(?<=data:image\/png;base64,)([\S]+)")
        
        b64_image_str:str = re.search(b64_regex, captcha_json["b64s"])[0]
        b64_image_bytes:bytes = bytes(b64_image_str, encoding = 'utf-8')
        
        captcha_id:str = captcha_json["id"]
        data_img = base64.b64decode(b64_image_bytes)
        
        if manual:
            return data_img, captcha_id
        
        from ddddocr import DdddOcr
        ocr = DdddOcr(show_ad = False)
        
        captcha = ocr.classification(data_img)

        self.set_captcha(captcha_id, captcha)
    
    def set_user(self, user_id:str, passward:str):
        self.user_id = user_id
        self.passward = passward
        
    def reset_user(self):
        self.user_id = ''
        self.passward = ''
        
    def set_captcha(self, captcha_id:str, captcha:str):
        self.captcha = captcha
        self.captcha_id = captcha_id
        
    def reset_captcha(self):
        self.captcha = ''
        self.captcha_id = ''
        
    def is_online(self):
        return not self.cookie_maintainer.is_expired()
        
    def is_running(self):
        return self.running
    
    @logger.catch
    @retry(retry = retry_if_exception(ValueError),
            stop  = stop_after_attempt(5),
            wait = wait_fixed(0.5),
            reraise = True)
    def create_session(self) -> Union [requests.Session, bool]:
        # Check the integrity of the params.
        if self.user_id == '' or self.passward == '':
            raise Exception("user_id or passward is not set")
        
        if self.token == '':
            self.get_token()
            
        if self.captcha == '' or self.captcha_id == '':
            logger.info("No available captcha, retrieving one...")
            self.get_captcha()
            
        target_url = r"https://v.ruc.edu.cn/auth/login"
        
        params = {
        "username"          : f"ruc:{self.user_id}",
        "password"          : f"{self.passward}",
        "code"              : f"{self.captcha}",
        "remember_me"       : "false",
        "redirect_url"      : "/",
        "twofactor_password": "",
        "twofactor_recovery": "",
        "token"             : f"{self.token}",
        "captcha_id"        : f"{self.captcha_id}"}
        
        headers = {'user-Agent': self.ua.random}
        
        session = requests.Session()
        server_response:requests.Response = session.post(url  = target_url,
                                    headers = headers,
                                    json    = params)
        
        response_text = server_response.text
        
        if response_text.startswith('{'):
            response_json = json.loads(response_text)
            
            if response_json["error_description"] == 'captcha error':
                logger.warning("captcha error, retrying...")
                self.reset_captcha()
                raise ValueError("captcha error")
            else:
                raise Exception(response_text["error_description"])
        logger.success("Re-establish session with remote server.")
        self.reset_captcha()
        return session
        
    def refresh_cookie(self):
        
        session = self.create_session()
        
        if session is None:
            return session
        cookie = session.cookies.get_dict()
        self.cookie_maintainer.update_content(cookie)
        return session
    
    def set_notify(self, notify: Methods):
        self.notify_method = notify
        self.notice = NOTIFIER[self.notify_method]
        
    def export_cookie(self) -> str:
        cookie = self.cookie_maintainer.get_content()
        if cookie is None:
            logger.warning("cookie expired, refreshing...")
            self.refresh_cookie()
            cookie = self.cookie_maintainer.get_content()
        
        return cookie
    
    # The following is about interact with server.
    
    def regist(self, lecture_id:str) -> str:
        regist_url = r"https://v.ruc.edu.cn/campus/Regist/regist"
        
        params = {"aid":lecture_id}
        headers = {'User-Agent': self.ua.random}
        
        response:Dict[str,str] = query_html(
            method = 'POST',
            url = regist_url,
            headers = headers,
            json = params,
            cookies = self.export_cookie()
        )
        
        return response["msg"]
    
    def notice(self, lectures: List[Dict]):
        pass

    def check_lecture(self,
                    max_lecture_num: int       = 30,
                    lecture_type   : List[str] = ["","",""],
                    query          : str       = "",
                    filter_function: Callable  = None) -> Tuple[int]: 
        """
        This function will pull lectures from ruc server with certain conditions and filter them.
        After that, it will maintain lecture observed, and try to register new lectures.

        Args:
            max_lecture_num (int, optional): _description_. Defaults to 30.
            lecture_type (List[str], optional): _description_. Defaults to [].
            query (str, optional): _description_. Defaults to "".
            filter (_type_, optional): _description_. Defaults to a simple function always returning True.
            
        >>> check_lecture(lecture_type = ["素质拓展认证","形势与政策","形势与政策讲座"])
        """
        
        self.locking = True
        
        def is_not_end(lecture_info: Dict[str,Union[str,Dict]]):

            end_time = lecture_info["registendtime"]
            regist_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            regist_over = regist_end_time > datetime.now()

            return regist_over
        
        if filter_function is None:
            filter_function = is_not_end
            
        logger.info("Checking lectures...")
            
        campus_url = r"https://v.ruc.edu.cn/campus/v2/search"
        
        headers = {'user-Agent': self.ua.random}
        
        params = {
        "perpage"      : max_lecture_num,
        "page"         : 1,
        "typelevel1"   : self.mapping[lecture_type[0]],
        "typelevel2"   : self.mapping[lecture_type[1]],
        "typelevel3"   : self.mapping[lecture_type[2]],
        "applyscore"   : 0,
        "begintime"    : "",
        "location"     : "",
        "progress"     : 0,
        "owneruid"     : "",
        "sponsordeptid": "",
        "query"        : query,
        "canregist"    : 0}
        
        response:Dict = query_html(
            method  = 'POST',
            url     = campus_url,
            headers = headers,
            json    = params,
            cookies = self.export_cookie())
        
        lectures = response['data']['data']
        
        lectures_filtered = list(filter(filter_function, lectures))
        
        new_lectures = [lec for lec in lectures_filtered if int(lec["aid"]) not in self.lecture_pool_checked]
        
        logger.info('Registering new {} lecture(s)'.format(len(new_lectures)))
        
        lectures_regist_success = []
        
        for lec in new_lectures:
            regist_result:str = self.regist(lec["aid"])
            
            if regist_result == "注册成功":
                lectures_regist_success.append(lec)
                
            duration = datetime.strptime(lec["registendtime"], "%Y-%m-%d %H:%M:%S") - datetime.now()
            
            duration_seconds = int(duration.total_seconds())
            lec_maintainer = Maintainer(duration_seconds)
            lec_maintainer.update_content(lec["aid"])
            
            self.lecture_pool_checked.add(lec_maintainer)
            
        # print(self.lecture_pool_checked)
        
        self.notice(lectures_regist_success)
        self.locking = False
        return len(new_lectures), len(lectures_regist_success)
    
    def save(self):
        with open(self.save_path, 'wb') as f:
            pickle.dump(self, f)
            
    def clear_pool(self):
        for maintainer in list(self.lecture_pool_checked):
            if maintainer.is_expired():
                logger.info('Removing Lecture {} from pool'.format(maintainer.get_content(force_get = True)))
                self.lecture_pool_checked.remove(maintainer)
            
    def run(self,
            checking_interval_seconds: int       = 120,
            clear_interval_seconds   : int       = 3600,
            max_lecture_num          : int       = 30,
            lecture_type             : List[str] = ["","",""],
            query                    : str       = "",
            filter_function          : Callable  = None
            ):
        
        schedule.every(checking_interval_seconds).seconds.do(self.check_lecture, max_lecture_num, lecture_type, query, filter_function)
        schedule.every(clear_interval_seconds).seconds.do(self.clear_pool)
        
        self.running = True
        
        try:
            while self.running:
                schedule.run_pending()
        except KeyboardInterrupt:
            logger.info("Encounter keyboard interrupt, exiting...")
            self.save()
            
        return
    
    def stop(self):
        self.running = False

