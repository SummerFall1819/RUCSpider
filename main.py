
import atexit

from components import RUCSpider

def save_spider(spider):
    spider.save()

def main():
    spider = RUCSpider()
    
    atexit.register(save_spider, spider)
    spider.user_id = '20xx'
    spider.passward = '[Your password]'
    spider.check_lecture(lecture_type = ["素质拓展认证","形势与政策","形势与政策讲座"], max_lecture_num = 30)
    spider.run(checking_interval_seconds = 10)

main()