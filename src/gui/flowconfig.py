import FlowConfigUi

from PyQt4 import QtGui, QtCore

class FlowConfig(QtGui.QDialog):
    def __init__(self, guimain):
        QtGui.QDialog.__init__(self)
        self.dialog = FlowConfigUi.Ui_Dialog()
        self.dialog.setupUi(self)
        self.connecthandlers()
        self.guimain = guimain
        
    def connecthandlers(self):
        self.dialog.buttonBox.accepted.connect(self.handle_accept)
        self.dialog.buttonBox.rejected.connect(self.handle_reject)
        
    def handle_accept(self):
        # save changes then hide
        
        print self.guimain.proxy
        
        # TODO: Save changes
        self.hide()
        
    def handle_reject(self):
        self.hide()