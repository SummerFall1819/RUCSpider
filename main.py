
import atexit
from getpass import getpass
from components import RUCSpider

from constants import DEFAULT_LECTURE

def save_spider(spider):
    spider.save()

def main():
    spider = RUCSpider()
    
    atexit.register(save_spider, spider)
    # spider.user_id = '20xx'
    # spider.passward = '[Your password]'
    
    if spider.user_id == '' or spider.passward == '':
        
        spider.user_id = input('Please enter your user id here:>')
        spider.passward = getpass('Please enter your password here:>')

    lecture_type = ["素质拓展认证","形势与政策","形势与政策讲座"]
    
    if lecture_type == DEFAULT_LECTURE:
        print("You are using the default lecture type. You may cahnge your lecture type by setting in code line 23. You can comment line 26 to hide this message.")
    
    spider.check_lecture(lecture_type = lecture_type, max_lecture_num = 30)
    spider.run(checking_interval_seconds = 10)

main()