
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