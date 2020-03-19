import sys
from . import clsm_pixel_select
from qtpy.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    gui = clsm_pixel_select.CLSMPixelSelect()
    gui.show()
    app.exec_()


if __name__ == "__main__":
    main()