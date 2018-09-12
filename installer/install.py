import logging
import os
import shutil
import stat
import subprocess
import sys

from PySide2 import QtCore, QtWidgets, QtGui

import utils

__author__ = 'Darragh Van Tichelen'


# Setup logging
logger = logging.getLogger('PlanarAllyInstaller')
logger.setLevel(logging.INFO)
if utils.get_os() != 'osx':
    fh = logging.FileHandler('planarallyinstall.log')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


# Catch every uncaught exception and log it.

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("UNCAUGHT EXCEPTION", exc_info=(
        exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


class PlanarAllyInstallGUI(QtWidgets.QWidget):
    """
    The main installer gui.
    """

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.start_thread = None
        self.progress_step = 0
        self.offset = None

        # Ignore Window Manager features (no frame, no min, max, close buttons)
        # this NEEDS to happen before the UI initialization!
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # without this obscure attribute the given background image wouldn't display.
        self.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.init_ui()
        self.setObjectName("Installer")
        self.setStyleSheet(
            r'#Installer { background-color: #fff; font-family: "Open Sans", sans-serif;}')

    def mousePressEvent(self, event):
        """
        Remember location of mouse pressed event to move the launcher.
        This is needed as we ignore the window manager.
        """
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """
        Move the installer!
        This is needed as we ignore the window manager.
        """
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def init_ui(self):
        """
        Init the UI. (duh)
        """
        title = QtWidgets.QLabel("PlanarAlly Server Installer", self)
        title.setGeometry(0, 0, 250, 50)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 15px; background-color: #FF7052; color: #fff;font-weight: bold;")

        close_button = QtWidgets.QPushButton('X', self)
        close_button.setGeometry(225, 0, 25, 25)
        close_button.setStyleSheet(
            "background-color: rgba(0,0,0,0);border:none;")
        close_button.clicked.connect(self.close)

        install_label = QtWidgets.QLabel("Install location:", self)
        install_label.setGeometry(25, 60, 225, 25)
        install_label.setStyleSheet(
            "font-size: 13px;")

        self.install_text = QtWidgets.QLineEdit(self)
        self.install_text.setGeometry(50, 85, 175, 20)
        self.install_text.setStyleSheet(
            "border-style: outset;border-width: 1px;border-radius: 8px;border-color: black"
            "beige;font: 12px;min-width: 5em;padding-left:5px")
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
        QtCore.QCoreApplication.setOrganizationName("PlanarAlly")
        defaultdir = os.path.dirname(QtCore.QSettings().fileName())
        if not os.path.isdir(defaultdir):
            os.makedirs(defaultdir)
        self.install_text.setText(defaultdir)

        folder_button = QtWidgets.QPushButton('', self)
        folder_button.setGeometry(225, 85, 20, 20)
        folder_button.setIcon(QtGui.QIcon(
            utils.resource_path("selectfolder.png")))
        folder_button.setStyleSheet(
            "background-color: rgba(0,0,0,0);border:none;")
        folder_button.clicked.connect(self.set_folder)

        start_button = QtWidgets.QPushButton('GO!', self)
        start_button.setGeometry(125, 120, 100, 20)
        start_button.setStyleSheet(
            """QPushButton {
                background-color: #fff;
                border:solid;
                border-radius:10px;
                border-width:1px;
                border-color:#FF7052
            }
            QPushButton:pressed, QPushButton:hover {
                background-color:#FF7052;
            }""")
        start_button.clicked.connect(self.start)
        start_button.setIcon(QtGui.QIcon(
            utils.resource_path("enter.png")))

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle("PlanarAlly Server Installer")
        self.show()

    def warn(self, title, text):
        """
        Warning popup shorthand.
        """
        QtWidgets.QMessageBox().warning(self, title, text)

    def set_folder(self):
        """
        Show a QFileDialog to set the installation folder.
        """
        folder_selector = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Installation folder", "",
                                                                     QtWidgets.QFileDialog.ShowDirsOnly)
        if os.path.isdir(folder_selector):
            self.install_text.setText(folder_selector)

    # noinspection PyUnresolvedReferences
    def start(self):
        """
        Start the install process after checking if the install directory is legit.
        """
        if not os.path.isdir(self.install_text.text()):
            self.warn("Install directory missing",
                      'The install directory provided is not a valid path.')
        else:
            install_directory = os.path.normpath(self.install_text.text())

            if self.start_thread:
                self.start_thread.terminate()

            self.start_thread = QtCore.QThread()
            # instantiate the backend.  backend_class should be provided by the OS specific context.
            self.backend = PAInstallBackend(install_directory)
            self.backend.moveToThread(self.start_thread)
            self.backend.finished.connect(self.finish)
            self.start_thread.started.connect(self.backend.start)
            self.start_thread.start()

    def finish(self):
        """
        Finalizes the install procedure.
        Stops the install thread.
        """
        self.start_thread.quit()
        sys.exit(0)


class PAInstallBackend(QtCore.QObject):
    finished = QtCore.Signal()

    def __init__(self, install_directory):
        super().__init__()
        self.install_directory = install_directory

    def start(self):
        python_version = "3.7.0"
        python_exec = "python-{}{}.exe".format(
            python_version, "-amd64" if utils.get_arch() == "64" else "")
        python_path = "{}/{}".format(python_version, python_exec)

        # 1: CD to the installation directory
        os.chdir(self.install_directory)

        # 2: Download python
        python_url = "https://www.python.org/ftp/python/{}/{}".format(
            python_version, python_exec)
        response = utils.download_file(python_url)
        utils.write_file(response.content, python_exec)

        # 3: Install python
        python_command = "{} /passive TargetDir={} AssociateFiles=0 Shortcuts=0 Include_doc=0 Include_dev=0 Include_launcher=0 InstallLauncherAllUsers=0 Include_tcltk=0 Include_test=0 Include_tools=0".format(
            python_exec, os.path.join(self.install_directory, 'python')
        )
        try:
            subprocess.check_call(self.python_command, shell=True)
        except subprocess.CalledProcessError:
            raise Exception("COULD NOT INSTALL PYTHON")

        # 4: Update pip
        print("4")
        try:
            subprocess.check_call(
                "{} -m pip install -U pip".format(python_path), shell=True)
        except subprocess.CalledProcessError:
            raise Exception("COULD NOT UPDATE PIP")

        # 5: Download master zip
        planarally_zip = "https://github.com/Kruptein/PlanarAlly/archive/master.zip"
        utils.download_zip(planarally_zip, self.install_directory, filter=[
            'PlanarAlly-master/requirements.txt', 'PlanarAlly-master/PlanarAlly'])

        # 6: pip install requirements
        try:
            subprocess.check_call(
                "{} -m pip install -r {}".format(python_path, "requirements.txt"), shell=True)
        except subprocess.CalledProcessError:
            raise Exception("COULD NOT UPDATE PIP")

        # : Remove install exe's

        # : Finish installation
        self.finished.emit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ll = PlanarAllyInstallGUI(app)
    sys.exit(app.exec_())
