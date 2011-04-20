import sys
import xmlrpclib
import time
import thread
import mutex
import HexEdit
import RuleGui
import InterfacesGui
import ProtocolsGui
import DbGui
import flowconfig
import rule
import muckpipe
import base64
import pickle
import Queue
import traceback
from PyQt4 import QtGui, QtCore, Qt
from Mallory import Ui_MainWindow
from debug import DebugEvent
from binascii import hexlify, unhexlify
from threading import Lock
import Pyro.core
import logging
import AboutDialog

from config import Config
# Pyro imports go here


class MalloryGui(QtGui.QMainWindow):
    
    iceptClicked = QtCore.pyqtSignal()
        
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.main =  Ui_MainWindow()
        self.flowconfig = flowconfig.FlowConfig(self)        
        self.app = None
        self.streammod = StreamTable(self)

        # Dialogs
        self.aboutdialog = AboutDialog.AboutDialog(self) 
                
        # Initialized after setupUi runs
        self.interfacesgui = None
        self.protocolsgui = None
        self.rulegui = None
        self.dbgui = None
        
        debugger_uri = "PYROLOC://127.0.0.1:7766/debugger"
        self.remote_debugger = Pyro.core.getProxyForURI(debugger_uri)
        
        #self.proxy = xmlrpclib.ServerProxy("http://localhost:20757")
        #self.objectproxy = xmlrpclib.ServerProxy("http://localhost:20758")
        self.curdebugevent = ""

        self.log = logging.getLogger("mallorygui")
        config = Config()
        config.logsetup(self.log)
        
    def connecthandlers(self):
        self.main.btnicept.clicked.connect(self.handle_interceptclick)
        self.main.btnsend.clicked.connect(self.handle_send)
        self.main.btnclear.clicked.connect(self.handle_clear_streams)
        self.main.tablestreams.activated.connect(self.handle_cellclick)
        self.main.tablestreams.clicked.connect(self.handle_cellclick)
        self.main.btnsavehex.clicked.connect(self.handle_savehex)
        self.main.btnsavetext.clicked.connect(self.handle_savetext)
        self.main.actionFlow_Config.triggered.connect(self.handle_menuflowconfig)
      
        self.main.btnauto.clicked.connect(self.updateStatusBar)
        self.main.actionAbout_Mallory.triggered.connect(self.handle_about)
    
        
    def handle_about(self):
        self.aboutdialog.show()
        print "Handling About"
           
    def setUp(self):
        self.hexedit = HexEdit.HexEdit(self.main.tablehex, self.app, self.statusBar())
        self.hexedit.ready = True 
        self.hexedit.setupTable()
        self.hexedit.loadData("QWERTYUDFGVBHNJDFGHJ")
        #status = self.statusBar()
        self.updateStatusBar()

                 
        #Create the object inspector
        #self.objectInspector = ObjectInspectorHandler(self.main.treeWidget_objectinspector, self.main.plainTextEdit_objectInspector, self.main.listWidget_objects)

        # Start the gui server
        #self.server = XMLRPCGuiServer(self.objectInspector)
        #self.server.start()
        
        #Let mallory know we are connected
        try:
            #self.objectproxy.connect()
            pass 
        except:
            self.log.error("Could not connect to object proxy RPC server");

        #Connect signals
        #self.server.objectReceived.connect(self.objectInspector.objectReceived)
                
    def setupModels(self):
        self.main.tablestreams.setModel(self.streammod)

    def handle_interceptclick(self):
        if self.main.btnicept.isChecked():
            self.remote_debugger.setdebug(True)     
        else:
            self.remote_debugger.setdebug(False)
        self.updateStatusBar()
        
    def updateStatusBar(self):
        self.main.statusbar.showMessage("Intercept: %s     Autosend: %s" % (str(self.main.btnicept.isChecked()), str(self.main.btnauto.isChecked())))
    
    def keyPressEvent(self, event):
        if int(event.key()) == ord('S'):
            self.handle_send()
         
    def handle_cellclick(self, index):
        streamdata = self.streammod.getrowdata(index.row())
        self.main.textstream.setPlainText(streamdata.data)
        self.hexedit.loadData(streamdata.data)
        self.curdebugevent = streamdata
                    
        #print "DATA FOR: %s" % (streamdata)
        
    def handle_savehex(self, checked):
        editdata = self.hexedit.getData()
        self.curdebugevent.data = editdata
        
    def handle_savetext(self, checked):
        editdata = self.main.textstream.toPlainText()
        self.curdebugevent.data = str(editdata)
        
    def handle_menuflowconfig(self, checked):
        self.flowconfig.show()
                         
    def handle_send(self):
        #print "OK DATA: " + self.main.textstream.toPlainText()
        #print "OK DATA: " + repr(str(self.main.textstream.toPlainText()))        
        # Send the current debug event       
        if self.main.btnauto.isChecked():
            warn = QtGui.QMessageBox.Warning 
            title = "Autosend is enabled"
            text = "Disable autosend before manually editing and sending events"                
            self.msgbox = QtGui.QMessageBox(warn, title, text)
            self.msgbox.show()                   
            return
        
        if self.send_cur_de(self.curdebugevent):
            print "GUI sending debug event:%s" % (self.curdebugevent)
            
    def handle_clear_streams(self):
        # TODO: Make thread safe (lock, prevent new debug requests from coming)
        self.streammod.requests = []
        self.streammod.reset()
        
        print "Clearing Streams"
        
    def send_cur_de(self, debugevent):
        if debugevent != "" and debugevent is not None:
            # Encode, and then decode, so the editors have the right data
            #debugevent['data'] = \
            #    str(debugevent['data']).encode("string-escape")
                        
            self.remote_debugger.send_de(debugevent)
            
            #debugevent['data'] = \
            #    str(debugevent['data']).decode("string-escape")
                            
            self.main.tablestreams.resizeColumnsToContents()
                        
            # This currently updates the entire model. Make this more efficient
            # by updating just the row that was sent. Performance seems OK
            # with a few hundred rows. 
            numrows = len(self.streammod.requests)
            numcolumns = len(self.streammod.columns)
            topleftidx = self.streammod.createIndex(0, 0)
            botrightidx = self.streammod.createIndex(numrows-1, numcolumns)
            self.main.tablestreams.dataChanged(topleftidx, botrightidx)
            
            for item in self.streammod.requests:
                if item.eventid == debugevent.eventid:
                    item.status = "S"
            return True
        
        return False
                                
    def check_for_de(self):
        print "[*] MalloryGui: Launching event check thread"
           
        eventcnt = 0
        while True:
            try:
                eventlist = self.remote_debugger.getdebugq()
                 
                # Currently only handling one selection 
                selections = self.main.tablestreams.selectionModel()
                selectlist = selections.selectedRows()   
             
                row = -1
                if len(selectlist) == 1:
                    selectindex = selectlist [0]
                    row = selectindex.row()
                                                
                eventsin = 0
                
                #for remoteitem in eventlist:
                #    print "Got remote event: %s:%s" % (remoteitem.__class__, remoteitem)
                    
                # Should be acquiring a mutex here
                for event in eventlist:                    
                    event.cnt = eventcnt
                    event.status = "U"

                    position = self.streammod.rowCount(None)
                    self.streammod.insertRows(position, 1, QtCore.QModelIndex(), event)
                    
                                             
                    eventsin += 1
                    eventcnt += 1
                                        
                    #print "%s:%s" % (event.__class__, event)
                    
#                if eventsin > 0:
#                    if row > -1:
#                        idx = self.streammod.createIndex(row, 0)
#                        self.main.tablestreams.setCurrentIndex(idx)

                # Should probably be releasing the mutex we should acquire here
                time.sleep(.1)
                
                while self.main.btnauto.isChecked():
                    next_unsent = self.streammod.get_next_unsent()
                    if not next_unsent:
                        break
                    #self.curdebugevent = next_unsent
                    self.send_cur_de(next_unsent)
                
            except:
                print "[*] MalloryGui: check_for_de: exception in de check loop"
                print sys.exc_info()
                traceback.print_exc()
         
class StreamListDelegate(QtGui.QItemDelegate):
    def __init__(self, parent, model):
        super(StreamListDelegate, self).__init__(parent)        
        self.model = model
            
    def paint(self, painter, option, index):
        rowdata = self.model.getrowdata(index.row())
        
        color = QtCore.Qt.white
        if "status" in rowdata.__dict__:
            if rowdata.status == "S":
                color = QtGui.QColor(204, 255, 204) # Light green
        else:                    
            color = QtGui.QColor(255, 204, 204) # Light red

        painter.save()
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.setBrush(QtGui.QBrush(color))
        painter.drawRect(option.rect)
        painter.restore()            
        QtGui.QItemDelegate.paint(self, painter, option, index)

class StreamTable(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(StreamTable, self).__init__(parent)
        self.columns = {
                   0: "Cnt",
                   1: "Dir",
                   2: "Len",
                   3: "Source",
                   4: "Dest",
                   5: "Status"
        }
        self.requests = []
        self.nrows = 5
           
    def getrowdata(self, row):    
        data = self.requests[row]
        return data
        
    def get_next_unsent(self):
        
        nextreq = None
        for request in self.requests:
            if request.status == "U":
                nextreq = request
            
        if nextreq:
            return nextreq
        
        return False
            
                                
    def rowCount(self, parent):        
        return len(self.requests)
    
    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(20, 20)
        
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section > -1 and section < len(self.columns):
                    return self.columns[section]
        
    def insertRows(self, position, numrows, index, event):
        #print "Inserting row @ %s with numrows=%s index=%s"%(str(position),str(numrows),str(index))
        
        self.beginInsertRows(QtCore.QModelIndex(), position, position+numrows-1)
        self.requests.append(event)
        self.endInsertRows()
        
    def setData(self, index, value):
        pass
    
    # Colors used in the table        
    bgCol_c2sSent = Qt.QColor(0xFBEDED)
    bgCol_s2cSent = Qt.QColor(0xEDEDFB)
    fgCol_unsent = Qt.QColor(0)
    fgCol_sent = Qt.QColor(0x555555)
    
    def saturate(self, color, amount = 40):
        """ Returns a color that is saturated wit the specified amount. If the amount is 
        negative, the color is desaturated"""
        # Get hue, saturation, value and alpha
        (h,s,v,a) = color.getHsv();
        s = s + amount
        if s > 255:
            s = 255
        if s < 0:
            s = 0
        return Qt.QColor.fromHsv(h, s, v, a)
    
    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        
        if role == QtCore.Qt.BackgroundRole:
            data = self.getrowdata(index.row())
            col = self.bgCol_c2sSent
            if data.direction == "s2c":
                col = self.bgCol_s2cSent

            if "status" in data.__dict__ and data.status == 'U':
                col = self.saturate(col)
            return QtCore.QVariant(col)
                    
        
        # Sent are greyed out a bit
        if role == QtCore.Qt.ForegroundRole:
            data = self.getrowdata(index.row())
            col = self.fgCol_unsent
            if "status" in data.__dict__ and data.status == 'S':
                col = self.fgCol_sent
            return QtCore.QVariant(col)
                            
        if role == QtCore.Qt.DisplayRole and index.isValid():
            data = self.getrowdata(index.row())

            if index.column() == 0:
                return data.cnt
            if index.column() == 1:
                return data.direction
            if index.column() == 2:
                return str(len(data.data))
            if index.column() == 3:
                return "%s:%s" % (data.source[0], data.source[1])
            if index.column() == 4:
                return "%s:%s" % (data.destination[0], data.destination[1])
            if index.column() == 5:
                if "status" in data.__dict__:
                    return data.status
                else:
                    return "U"                
            if index.column() == 5:
                return data.eventid
        else:
            return QtCore.QVariant()                   

def main():
    app = QtGui.QApplication(sys.argv)
    window = MalloryGui()    
    window.app = app    
    window.main.setupUi(window) 
    window.connecthandlers()
    window.setUp()
    window.setupModels()
    
  
    # Interfaces Editor GUI (self contained in interfaces tab)
    window.interfacesgui = \
        InterfacesGui.InterfacesGui(window.main.tableinterfaces,
                                    window.main.btnsaveifcfg,
                                    window.main.btnrefreshifaces)
    
    # Protocols Editor GUI (self contained in protocols tab)
    window.protocolsgui = \
        ProtocolsGui.ProtocolsGui(window.main.tableprotocols,
                                  window.main.btnprotoreload,
                                  window.main.btnprotoapply,
                                  window.main.textprotoedit,
                                  window.main.splitterproto)
        
    # Database view GUI
    window.dbgui = DbGui.DbGui(window.main.tabledbview,
                               window.main.btndbexec,
                               window.main.btndbflowsq,
                               window.main.textdbsql,
                               window.main.splitter_db)
    
    
    window.rulegui = RuleGui.RuleEdit(window.main)
        
    #window.main.tab_protocols
    # Kick off debug event loop in a separate thread
    thread.start_new_thread(window.check_for_de, ())
    
    window.main.tablestreams.resizeColumnsToContents()
    window.main.tablestreams.resizeRowsToContents()
        
    window.show()
    
    sys.exit(app.exec_()) 
          
if __name__ == "__main__":
    main()
