# Compile the .ui XML into a .py file suitable for use w/pyqt
pyuic = pyuic4
pyrcc = pyrcc4

.PHONY : gui
gui:
	$(pyuic) gui/Mallory.ui > gui/Mallory.py
	$(pyuic) gui/TextViewDialog.ui > gui/TextViewDialogUi.py
	$(pyuic) gui/AboutDialog.ui > gui/AboutDialogUi.py
	$(pyrcc) gui/mallory_gui.qrc > gui/mallory_gui_rc.py
