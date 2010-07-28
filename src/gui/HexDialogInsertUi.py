# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'HexDialogInsert.ui'
#
# Created: Tue Jun  1 23:39:31 2010
#      by: PyQt4 UI code generator 4.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_HexDialogInsert(object):
    def setupUi(self, HexDialogInsert):
        HexDialogInsert.setObjectName("HexDialogInsert")
        HexDialogInsert.resize(404, 146)
        self.verticalLayout = QtGui.QVBoxLayout(HexDialogInsert)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtGui.QWidget(HexDialogInsert)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.radioHex = QtGui.QRadioButton(self.widget)
        self.radioHex.setObjectName("radioHex")
        self.horizontalLayout.addWidget(self.radioHex)
        self.lblhex = QtGui.QLabel(self.widget)
        self.lblhex.setObjectName("lblhex")
        self.horizontalLayout.addWidget(self.lblhex)
        self.lineHex = QtGui.QLineEdit(self.widget)
        self.lineHex.setObjectName("lineHex")
        self.horizontalLayout.addWidget(self.lineHex)
        self.verticalLayout.addWidget(self.widget)
        self.widget_2 = QtGui.QWidget(HexDialogInsert)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.radioText = QtGui.QRadioButton(self.widget_2)
        self.radioText.setChecked(True)
        self.radioText.setObjectName("radioText")
        self.horizontalLayout_2.addWidget(self.radioText)
        self.lbltxt = QtGui.QLabel(self.widget_2)
        self.lbltxt.setObjectName("lbltxt")
        self.horizontalLayout_2.addWidget(self.lbltxt)
        self.lineText = QtGui.QLineEdit(self.widget_2)
        self.lineText.setObjectName("lineText")
        self.horizontalLayout_2.addWidget(self.lineText)
        self.verticalLayout.addWidget(self.widget_2)
        self.buttonBox = QtGui.QDialogButtonBox(HexDialogInsert)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(HexDialogInsert)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), HexDialogInsert.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), HexDialogInsert.reject)
        QtCore.QMetaObject.connectSlotsByName(HexDialogInsert)

    def retranslateUi(self, HexDialogInsert):
        HexDialogInsert.setWindowTitle(QtGui.QApplication.translate("HexDialogInsert", "Insert Bytes", None, QtGui.QApplication.UnicodeUTF8))
        self.lblhex.setText(QtGui.QApplication.translate("HexDialogInsert", "Hex String", None, QtGui.QApplication.UnicodeUTF8))
        self.lbltxt.setText(QtGui.QApplication.translate("HexDialogInsert", "Text String", None, QtGui.QApplication.UnicodeUTF8))

