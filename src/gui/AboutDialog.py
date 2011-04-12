from PyQt4 import QtGui, QtCore, Qt
import AboutDialogUi

class AboutDialog(QtGui.QDialog):
    """
    This class creates a dialog that is used to capture and then insert a Hex or
    Text string into the data being edited.
    """
    def __init__(self, hexedit):
        QtGui.QDialog.__init__(self)
        self.dialog = AboutDialogUi.Ui_MainDialog()
        self.dialog.setupUi(self)
        
    def setText(self, text):
        self.dialog.textview.setPlainText(text)