from subprocess import run
from threading import Lock
from PySide2.QtCore import QObject, QRunnable, QThread, QThreadPool, Signal
from PySide2.QtWidgets import QApplication, QBoxLayout, QHBoxLayout, QWidget
from PySide2.QtCore import Qt
import mpv
import keyboard
import locale
import PySide2.QtCore as QtCore
import sys
import os
import pyautogui
import GiftUi

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class QTSignals(QObject):
    finished = Signal()

class Waiter(QThread):
    def __init__(self, player:mpv.MPV):
        super().__init__()
        self.player = player
        self.signals = QTSignals()

    def run(self):
        self.player.wait_for_playback()
        self.signals.finished.emit()
        
class DisableCursorMovements(QThread):
    def __init__(self, lock_cursor) -> None:
        super().__init__()
        pyautogui.FAILSAFE = False
        # Center Primary Screen Coordinates PySide2
        screen = QApplication.primaryScreen().geometry().center()
        self.x = screen.x()
        self.y = screen.y()
        self.lockcursor = lock_cursor
        pyautogui.moveTo(self.x, self.y)

    def run(self):
        while self.lockcursor:
            x, y = pyautogui.position()
            pyautogui.moveTo(self.x, self.y)

    def stop(self):
        self.lockcursor = False


class Player(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.debug = False
        self.signals = QTSignals()
        locale.setlocale(locale.LC_NUMERIC, 'C')
        layout = QHBoxLayout(self)
        layout.setMargin(0)
        self.threadpool = QThreadPool()
        self.player_running = False
        self.lock_cursor = False
        # Modifiers
        self.modifiers = ['alt', 'ctrl', 'shift', 'windows', 'tab']

        # Flags
        self.setStyleSheet("background-color: black;")
        flags = Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        # MPV Container
        self.container = QWidget(self)
        self.container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.container.setAttribute(Qt.WA_NativeWindow)
        self.player = mpv.MPV(wid=str(int(self.container.winId())))
        layout.addWidget(self.container)


    
    def play(self):
        self.windowHandle().setScreen(QApplication.primaryScreen())
        self.showFullScreen()
        self.player.play(resource_path('video.mp4'))
        self.waiter = Waiter(self.player)
        self.waiter.signals.finished.connect(self.exit)
        self.player.wait_until_playing()
        self.player_running = True
        self.waiter.start()
        self.lock_cursor = True
        self.centercursorer = DisableCursorMovements(lock_cursor=self.lock_cursor)
        if self.debug == False:
            self.setCursor(Qt.BlankCursor)
            self.disable_modifier_buttons()
            self.centercursorer.start()
        else:
            self.player.seek("00:01:13.00", reference="absolute")

    def exit(self):
        if self.debug == False:
            self.centercursorer.stop()
            self.enable_modifier_buttons()
        self.player.terminate()
        self.signals.finished.emit()
        self.close()

    def disable_modifier_buttons(self):
        for modifier in self.modifiers:
            keyboard.block_key(modifier)
    
    def enable_modifier_buttons(self):
        for modifier in self.modifiers:
            keyboard.unblock_key(modifier)

class GiftBox(QWidget):
    def __init__(self):
        super().__init__()
        self.playerwidget = Player()
        self.ui = GiftUi.Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("Gift Box")
        self.show()
        self.playerwidget.signals.finished.connect(self.exit)
        self.ui.pushButton.clicked.connect(self.run)
    
    def run(self):
        self.playerwidget.play()
        self.hide()
    
    def exit(self):
        self.hide()
        self.close()
        app.closeAllWindows()
        app.exit()

if "__main__" == __name__:
    app = QApplication(sys.argv)
    window = GiftBox()
    # window = Player()
    # window.show()
    app.exec_()

