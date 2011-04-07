import sys
import xmlrpclib
import time
import thread
import mutex
import HexEdit
import RuleGui
import InterfacesGui
import ProtocolsGui
import flowconfig
import rule
import muckpipe
import base64
import pickle
import Queue
import traceback
from PyQt4 import QtGui, QtCore, Qt
from TCPEdit import Ui_MainWindow
from debug import DebugEvent
from binascii import hexlify, unhexlify
from threading import Lock
import Pyro.core
import logging
from config import Config
# Pyro imports go here

#TODO: Refactor into separate class
class ObjectInspectorHandler():
    """This is a little handler for the object inspector tab. This in moved outside of MalloryGui to
    make less cluttering. MalloryGui sends in the relevant graphical compontents in init."""

    def __init__(self, treewidget, textedit, listwidget):
        self.treeWidget = treewidget
        self.textEdit = textedit
        self.listwidget = listwidget
        self.connectHandlers()
        object = {"foo":{"bar":"gazonk"}}
        self.setObject(object)
        self.objects= []
        listwidget.currentRowChanged.connect(self.changeRow)

    def changeRow(self, row):
        if row  > -1:
            self.setObject(self.objects[row])

    def setObject(self, object):
        self.object = object
        self.treeWidget.clear()
        root = QtGui.QTreeWidgetItem(self.treeWidget,["<Object>","HTTP"])
        self.treeWidget.expandItem(root)
        self._recurse(self.object, root)

    def addObject(self, object):
        self.objects.append(object)

        objdesc = "Object %d" % (len(self.objects))
        if "command" in object and "path" in object:
            objdesc = "HTTP[%d]: %s %s" % (len(self.objects),
                object["command"], object["path"][0:64])

        print "Adding object!"

        self.listwidget.addItem(objdesc)

    def connectHandlers(self):
        self.treeWidget.currentItemChanged.connect(self.updateDisplay)

    def updateDisplay(self):
        self.textEdit.setPlainText("")
        if self.object is None: return

        item = self.treeWidget.currentItem()
        if item is None: return
        path = [str(item.text(0))]
        while item.parent() is not None:
            item = item.parent()
            print item
            path.append(str(item.text(0)))

        path.reverse()
        #Remove the root node, that is the object itself
        path = path[1:]

#        print("Path: %s" % path)
        obj = self.object
        for x in path:
            obj=obj[x]
        self.textEdit.setPlainText(str(obj))

    def _recurse(self, object, root):
        """Recurses through the given object and fills the qtreeview
        with data"""
        # It may be an object or a dict
        if type(object).__name__ == 'instance':
            object = object.__dict__
        #Now we are dealing with a dict    
        for (k,v) in object.items():
            if type(v).__name__ <> 'instance' and type(v).__name__ <> 'dict':
                _v = str(v)
                if len(_v) > 50 :
                    _v = _v[:50]+ "..."
                item = Qt.QTreeWidgetItem(root, [str(k), _v])
            else:
                child = Qt.QTreeWidgetItem(root,[ str(k)])
                self.treeWidget.expandItem(child)
                self._recurse(v, child)

# RPCF - This method will have to be replaced to use Pyro             
#class XMLRPCGuiServer(Qt.QThread):
#    """The XMLRPCGuiServer is a server for the GUI where the mallory application
#    can push events"""
#
#    #This signal is emitted when objects are received
#    objectReceived = Qt.SIGNAL("objectReceived")
#
#    def __init__(self, objectReceiver):
#        Qt.QThread.__init__(self)
#        self.objectReceiver = objectReceiver
#        self.log = logging.getLogger("mallorygui")
#
#    def run(self):
#        try:
#            self.log.info("GUI: starting XML RPC Server")
#            server = SimpleXMLRPCServer(addr=("localhost", 20759), logRequests=False, allow_none=1)
#            server.register_function(self.pushObject, "push")
#            server.serve_forever()
#        except:
#            self.log.error("GUI: rpcserver: error connecting to remote")
#            self.log.error(sys.exc_info())
#
#    def pushObject(self, object):
#        """Objects are pushed here form the object editor implementation """
#        self.objectReceiver.addObject(object)
#        #self.emit(self.objectReceived)

class MalloryGui(QtGui.QMainWindow):
    
    iceptClicked = QtCore.pyqtSignal()
        
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.main =  Ui_MainWindow()
        self.flowconfig = flowconfig.FlowConfig(self)        
        self.app = None
        self.streammod = StreamTable(self)
        self.rulemod = RuleGui.RuleList(self)
                
        # Initialized after setupUi runs
        self.interfacesgui = None
        self.protocolsgui = None
        
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
        self.main.tablestreams.activated.connect(self.handle_cellclick)
        self.main.tablestreams.clicked.connect(self.handle_cellclick)
        self.main.btnsavehex.clicked.connect(self.handle_savehex)
        self.main.btnsavetext.clicked.connect(self.handle_savetext)
        self.main.actionFlow_Config.triggered.connect(self.handle_menuflowconfig)
        self.main.listrules.activated.connect(self.handle_ruleactivated)
        self.main.listrules.clicked.connect(self.handle_ruleactivated)
        self.main.saverule.clicked.connect(self.handle_saverule)
        self.main.buttondown.clicked.connect(self.handle_ruledown)
        self.main.buttonup.clicked.connect(self.handle_ruleup)
        self.main.buttonaddrule.clicked.connect(self.handle_ruleadd)
        self.main.buttondelrule.clicked.connect(self.handle_ruledel)        
        self.main.btnauto.clicked.connect(self.updateStatusBar)
        
    def setUp(self):
        self.hexedit = HexEdit.HexEdit(self.main.tablehex, self.app, self.statusBar())
        self.hexedit.ready = True 
        self.hexedit.setupTable()
        self.hexedit.loadData("QWERTYUDFGVBHNJDFGHJ")
        #status = self.statusBar()
        self.updateStatusBar()
        # Rules come in base64 encoded and pickled
        rules = self.remote_debugger.getrules()
        
        for rule in rules:
            print("MalloryGui.setUp: %s" % (str(rule)))
        
        self.rulemod.rules = rules
        
        self.ruleedit = RuleGui.RuleEdit(self.main, self.rulemod) 
        #Create the object inspector
        self.objectInspector = ObjectInspectorHandler(self.main.treeWidget_objectinspector, self.main.plainTextEdit_objectInspector, self.main.listWidget_objects)

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
        self.main.listrules.setModel(self.rulemod)

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
            

                           
    ##### See RuleGui.py for these methods
    def handle_ruleadd(self):
        self.ruleedit.handle_ruleadd()
        self.remote_debugger.updaterules(self.ruleedit.get_enc_rulepickle())
    def handle_ruledel(self):
        self.ruleedit.handle_ruledel()
        self.remote_debugger.updaterules(self.ruleedit.get_enc_rulepickle())           
    def handle_ruledown(self):
        self.ruleedit.handle_ruledown()
        self.remote_debugger.updaterules(self.ruleedit.get_enc_rulepickle())        
    def handle_ruleup(self):
        self.ruleedit.handle_ruleup()
        self.remote_debugger.updaterules(self.ruleedit.get_enc_rulepickle())        
    def handle_ruleactivated(self, index):
        self.ruleedit.handle_ruleactivated(index)        
    def handle_saverule(self):
        rules = self.ruleedit.handle_saverule()
        print rule       
        self.remote_debugger.updaterules(rules)       
        
    
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
        
    #window.main.tab_protocols
    # Kick off debug event loop in a separate thread
    thread.start_new_thread(window.check_for_de, ())
    
    window.main.tablestreams.resizeColumnsToContents()
    window.main.tablestreams.resizeRowsToContents()
        
    window.show()
    
    sys.exit(app.exec_()) 
          
if __name__ == "__main__":
    main()
