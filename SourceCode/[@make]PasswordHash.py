import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from gui import PasswordHashWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PasswordHashTool")
    app.setFont(QFont("メイリオ", 10)) 
    win = PasswordHashWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
