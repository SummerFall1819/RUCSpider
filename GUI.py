import os
import sys
import pickle
from typing import Dict
from time import sleep


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal

from Ui_login import Ui_LoginWindow
from Ui_spider import Ui_MainWindow

from components import RUCSpider, SelectorManager

        
class LoginWindow(QtWidgets.QMainWindow, Ui_LoginWindow):
    
    # The signal was sent to spider_window with id,pwd,code,captcha_id
    LoginInfoSignal = pyqtSignal(str,str,str,str)
    
    def __init__(self, spider:RUCSpider, close_signal:pyqtSignal):
        """
        Args:
            spider (_type_): the spider.
            close_signal (_type_): message of controlling close of the window.
        """
        super(QtWidgets.QMainWindow,self).__init__()
        self.setupUi(self)
        
        # Attributes.
        self.captcha_id = ''
        self.spider = spider
        
        # Connect functions to three buttons.
        self.LoginButton.clicked.connect(self.login)
        self.ResetButton.clicked.connect(self.resetinfo)
        self.ChangeButton.clicked.connect(self.get_captcha)
        
        if self.spider.user_id != '':
            self.user_id_input.setText(self.spider.user_id)
        if self.spider.passward != '':
            self.passward.setText(self.spider.passward)
        # Set the windoow always on top.
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # Control the close of the window.
        close_signal.connect(self.check)
        
    def show(self):
        """
        Rewrite the show function. We need to load a captcha first.
        """
        self.get_captcha()
        super().show()
        
    def get_captcha(self):
        """
        Load a captcha and show it on the window.
        It also used as updating a new captcha.
        """

        data_img, captcha_id = self.spider.get_captcha(manual=True)
        
        pix = QPixmap()
        pix.loadFromData(data_img)
        
        self.Image.setScaledContents(True)
        self.Image.setPixmap(pix)
        
        self.captcha_id = captcha_id
        
    def check(self, status:int):
        """
        Check the status of the main window, and close the login windows.
        
        If status == 1. We close the window.
        If status == 0. We show a warning box, and reset the whole window.

        Args:
            status (int): 
        """
        if status == 1:
            self.close()
        elif status == 0:
            QtWidgets.QMessageBox(Warning, '错误', '无法登录', QtWidgets.QMessageBox.Yes)
            self.resetinfo()
        else:
            self.close()
        
    def login(self):
        """
        Get the user input and send it to the main window, checking if could login in and establish a connection.

        This function passes 
        [user_id, passward_str, captcha_code, captcha_id] to the main window.
        """
        user_id = self.user_id_input.text()
        passward_str = self.passward.text()
        captcha_code = self.captcha.text()
        
        self.LoginInfoSignal.emit(user_id, passward_str, captcha_code, self.captcha_id)
    
    def resetinfo(self):
        """
        Reset the information of the window.
        """
        self.user_id_input.clear()
        self.passward.clear()
        self.captcha.clear()


class SpiderWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    
    # Trigger the login window.
    LoginSignal = pyqtSignal(int)
    
    def __init__(self,spider:RUCSpider):
        """
        The initialization of the main window is considered as:
        1. Set up all the UI.
        2. set the initial state of the window.
        3. binding slots to the widgets.
            1) The login and logout Action from menu bar.
            2) The combo boxes.
            3) The buttons.
            4) The updates of the reports.
        4. Check whether the spider is online, if not, show a login window.
        5. Check user's preference, and load in the params.

        Args:
            spider (RUCSpider): The spider which perform core functions.
        """
        # Set up the UIs.
        super(QtWidgets.QMainWindow, self).__init__()
        self.setupUi(self)
        
        # Hide the params and report part of the window.
        self.setVisibleReport(False)
        self.setVisibleParams(False)
        
        # Disable some buttons.
        self.PauseButton.setEnabled(False)
        
        # Set some params.
        self.spider = spider
        
        if os.path.exists('pref.pkl'):
            with open('pref.pkl','rb') as f:
                self.pref:Dict = pickle.load(f)
        else:
            self.pref:Dict = {
                "selectors":["不限", "不限", "不限"],
                "interval": self.retrieve_interval.value(),
                "max_retrieve_num": self.max_retrieve.value(),
                "query_str": self.Query_var.text(),
                "Notifier": '无',
                "apptoken": '',
                "UID": ''
                }
        
        # binding functions.
        # Menu bar:
        self.login_window = LoginWindow(self.spider, self.LoginSignal)
        self.actionLogin.triggered.connect(self.show_login)
        self.actionLogout.triggered.connect(self.logout)
        
        # combo boxes:
        self.selections = SelectorManager()
        #self.selectors = ["不限", "不限", "不限"]
        self.selectors = self.pref["selectors"]
        
        for items in self.selections.get_childrens(self.selectors[:0]):
            self.BigClass.addItem(items)
        for items in self.selections.get_childrens(self.selectors[:1]):
            self.SmallClass.addItem(items)
        for items in self.selections.get_childrens(self.selectors[:2]):
            self.SubClass.addItem(items)
        
        self.BigClass.setCurrentText(self.selectors[0])
        self.SmallClass.setCurrentText(self.selectors[1])
        self.SubClass.setCurrentText(self.selectors[2])
            
        self.BigClass.currentTextChanged.connect(self.updateSmallClass)
        self.SmallClass.currentTextChanged.connect(self.updateSubClass)
        self.Notifier.currentTextChanged.connect(self.updateParams)
        
        # The buttons:
        self.startButton.clicked.connect(self.start_spider)
        self.PauseButton.clicked.connect(self.pause_spider)
        
        # The reports update:
        self.timer = QtCore.QTimer()
        self.InitReportDatas()
        self.timer.timeout.connect(self.update_report)
        self.report_format = "运行总时长：{hour:02d}:{minute:02d}:{second:02d} 拉取次数：{pull_time:d} 新讲座数目：{new_lecs:02d} 成功报名数目：{regist_lecs:02d}"
        
        # Check online.
        self.login_window.LoginInfoSignal.connect(self.login)
        
        if self.spider.is_online() == False:
            self.WelcomeText.setText("请首先通过登录框登录。")
            self.login_window.show()
        else:
            self.WelcomeText.setText("欢迎回来，用户 {user_id}！".format(user_id = self.spider.user_id))
            
        # Set preferences.
        self.retrieve_interval.setValue(self.pref["interval"])
        self.max_retrieve.setValue(self.pref["max_retrieve_num"])
        self.Query_var.setText(self.pref["query_str"])
        self.Notifier.setCurrentText(self.pref["Notifier"])
        if self.pref["Notifier"] == "WxPusher":
            self.setVisibleParams(True)
            self.appToken.setText(self.pref["apptoken"])
            self.UID.setText(self.pref["UID"])
            
    # Util function begins.
    def InitReportDatas(self):
        """
        Initialize (or reset) the report datas.
        """
        self.current_round_time: int = 0
        self.total_time        : int = 0
        self.pull_time         : int = 0
        self.new_lecs          : int = 0
        self.regist_lecs       : int = 0
        self.interval          : int = 0
        self.max_retrieve_num  : int = 0
        self.query_str         : str = ''
        self.show_report       :bool = False
        
    def setVisibleReport(self, is_visible: bool):
        """
        show or hide the report part of the window.
        
        Args:
            is_visible (bool):
        """
        self.pBar.setVisible(is_visible)
        self.BarHeader.setVisible(is_visible)
        self.TimeSpan.setVisible(is_visible)
        self.AbstractInfo.setVisible(is_visible)
        self.show_report = is_visible
        
    def setVisibleParams(self, is_visible: bool):
        """
        Show of hide the params (for WxPusher) of the window.
        This part is only visible if you choose to use WxPusher.

        Args:
            is_visible (bool): _description_
        """
        self.Params.setVisible(is_visible)
        self.appToken.setVisible(is_visible)
        self.UID.setVisible(is_visible)
        
    def setVisibleChoose(self, is_visible: bool):
        """
        hide the choose part of the window.

        Args:
            is_visible (bool): _description_
        """
        self.BC_text.setVisible(is_visible)
        self.SC_text.setVisible(is_visible)
        self.SC_text_2.setVisible(is_visible)
        self.MR_text.setVisible(is_visible)
        self.RI_text.setVisible(is_visible)
        self.BigClass.setVisible(is_visible)
        self.SmallClass.setVisible(is_visible)
        self.SubClass.setVisible(is_visible)
        self.max_retrieve.setVisible(is_visible)
        self.retrieve_interval.setVisible(is_visible)
        self.Query_text.setVisible(is_visible)
        self.Query_var.setVisible(is_visible)
        self.Notify_text.setVisible(is_visible)
        self.Notifier.setVisible(is_visible)
        self.Params.setVisible(is_visible)
        self.WelcomeText.setVisible(is_visible)
        if not is_visible:
            self.setVisibleParams(False)
            self.appToken.setVisible(is_visible)
            self.UID.setVisible(is_visible)
        if is_visible and self.Notifier.currentText() == "WxPusher":
            self.setVisibleParams(True)
        
    # Util function ends.
        
    # Default function rewrite begins.
    def closeEvent(self,event):
        """
        When close the window, the remained login window will be closed as well.
        it also save the information from spider, and the reference of the user.
        """
        self.spider.save()
        self.LoginSignal.emit(True)
        
        preferences = {
            "selectors": [self.BigClass.currentText(), self.SmallClass.currentText(), self.SubClass.currentText()],
            "interval": self.retrieve_interval.value(),
            "max_retrieve_num": self.max_retrieve.value(),
            "query_str": self.Query_var.text(),
            "Notifier": self.Notifier.currentText(),
            "apptoken": self.appToken.text(),
            "UID": self.UID.text()
        }
        
        with open("pref.pkl","wb") as f:
            pickle.dump(preferences, f)

        event.accept()
        
    def resizeEvent(self, event):
        # 435 pixel
        # 860 pixel
        height = event.size().height()
        width = event.size().width()
        
        if height < 440 and self.show_report:
            self.setVisibleChoose(False)
            super().resizeEvent(event)
        else:
            self.setVisibleChoose(True)
            
        if width < 900 and self.show_report:
            
            self.report_format = "{hour:02d}:{minute:02d}:{second:02d}|{pull_time:04d}|{regist_lecs:02d}/{new_lecs:02d}"
            self.BarHeader.setVisible(False)
            super().resizeEvent(event)
        else:
            self.report_format = "运行总时长：{hour:02d}:{minute:02d}:{second:02d} 拉取次数：{pull_time:d} 新讲座数目：{new_lecs:02d} 成功报名数目：{regist_lecs:02d}"
            if self.show_report:
                self.BarHeader.setVisible(True)
    # Default function rewrite ends.
        
    # Menu Bar methods begins.
    def show_login(self):
        """
        Show the login window.
        """
        self.login_window.show()
        
    def login(self,user_id, passward_str, captcha_code,captcha_id):
        """
        The login function is bound with the LoginInfo Signal.
        The login window will return these params back, which will used in login.
        Refer to LoginWindow.login function.
        
        spider will use these params to try to login. After that it will try to update a cookie.
        If the login is successful, it'll emit a signal and close the login window.
        Otherwise, it'll emit a signal and show the error message box.
        """
        self.spider.set_user(user_id = user_id, passward = passward_str)
        self.spider.set_captcha(captcha_id = captcha_id, captcha = captcha_code)
        
        session = self.spider.refresh_cookie()
        if session is None:
            self.LoginSignal.emit(False)
        else:
            self.WelcomeText.setText("欢迎，用户 {user_id}！".format(user_id = self.spider.user_id))
            self.LoginSignal.emit(True)
            
    def logout(self):
        """
        The logout function will:
        1) If the spider is running, it will stop the spider from running.
        2) reset the report informations.
        3) hide the report part.
        4) reset the spider.
        5) reset the welcome text.
        """
        self.pause_spider()
        self.InitReportDatas()
        self.setVisibleReport(False)
        self.spider.reset_user()
        self.spider.reset_captcha()
        self.WelcomeText.setText("请首先通过登录框登录。")
    # Menu Bar methods ends.
    
    # Combo box methods begins.
    def updateSmallClass(self):
        self.SmallClass.clear()
        
        self.selectors = [self.BigClass.currentText(),"不限","不限"]

        for items in self.selections.get_childrens(self.selectors[:1]):
            self.SmallClass.addItem(items)
        
        for items in self.selections.get_childrens(self.selectors[:2]):
            self.SubClass.addItem(items)
            
    def updateSubClass(self):
        self.SubClass.clear()

        self.selectors = [self.BigClass.currentText(),self.SmallClass.currentText(),"不限"]
        
        for items in self.selections.get_childrens(self.selectors[:2]):
            self.SubClass.addItem(items)
            
    def updateParams(self):
        if self.Notifier.currentText() == "WxPusher":
            self.setVisibleParams(True)
        else:
            self.setVisibleParams(False)
    # Combo box methods ends.
    
    # Process methods begins.
    def start_spider(self):
        self.timer.start(1000)
        self.startButton.setEnabled(False)
        self.PauseButton.setEnabled(True)
        self.setVisibleReport(True)
        
        self.selectors = [self.BigClass.currentText(), self.SmallClass.currentText(), self.SubClass.currentText()]
        self.interval = self.retrieve_interval.value()
        self.max_retrieve_num = self.max_retrieve.value()
        self.query_str = self.Query_var.text()
        
    def pause_spider(self):
        while self.spider.locking:
            sleep(1)
        
        self.update_report()
        self.timer.stop()
        self.startButton.setEnabled(True)
        self.PauseButton.setEnabled(False)
        
    # Process methods ends.
    
    # Report part methods begins.
    def update_process(self):
        self.current_round_time += 1
        if self.current_round_time > self.interval:
            self.current_round_time = 1
            
        self.pBar.setValue( int(self.current_round_time / self.interval * 100) )
        self.TimeSpan.setText('{cMinute:02d}:{cSecs:02d}/{tMinute:02d}:{tSecs:02d}'.format(
            cMinute = self.current_round_time // 60,
            cSecs = self.current_round_time % 60,
            tMinute = self.interval // 60,
            tSecs = self.interval % 60
        ))
        
        if self.current_round_time == self.interval:
            all_lec, success_lec = self.spider.check_lecture(
                max_lecture_num = self.max_retrieve_num,
                lecture_type = self.selectors,
                query = self.query_str,
            )
            self.pull_time += 1
            self.new_lecs += all_lec
            self.regist_lecs += success_lec
        

    def update_report(self):
        self.update_process()
        # self.current_round_time += 1
        self.total_time += 1
        self.AbstractInfo.setText(self.report_format.format(
            hour = self.total_time // 3600,
            minute = (self.total_time % 3600) // 60,
            second = (self.total_time % 3600) % 60,
            pull_time = self.pull_time,
            new_lecs = self.new_lecs,
            regist_lecs = self.regist_lecs)
        )
        
        if self.total_time % 3600 == 0:
            self.spider.clear_pool()
    # Report part methods ends.
    
    


if __name__ == '__main__':

    spider = RUCSpider()
    app = QtWidgets.QApplication((sys.argv))
    window = SpiderWindow(spider)
    window.show()
    sys.exit(app.exec_())
