from PyQt4 import QtGui, QtCore, Qt
import Pyro.core

class ProtocolsGui(object):
    """
    Controller and model for the protocol management GUI
    """
    def __init__(self, protocols_table, btn_reload, btn_apply, 
                 text_proto_edit):
        self.protocols_table_view = protocols_table                
        self.btn_reload = btn_reload
        self.btn_apply = btn_apply
        self.text_proto_edit = text_proto_edit
                
        # Remote protocol configuration object
        config_protocols_uri = "PYROLOC://127.0.0.1:7766/config_proto"
        self.remote_proto = \
            Pyro.core.getProxyForURI(config_protocols_uri)
        
        # Setup model for table view    
        self.protocols_model = ProtocolsTableModel(self.remote_proto)
        self.protocols_table_view.setModel(self.protocols_model)
                
        # Load initial config
        self.handle_proto_reload()

        # Wire up event handlers
        self.connect_handlers()

    def connect_handlers(self):
        self.btn_apply.clicked.connect(self.handle_proto_apply)
        self.btn_reload.clicked.connect(self.handle_proto_reload)
        
    def handle_proto_apply(self):
        raw_text = self.text_proto_edit.toPlainText()
        self.remote_proto.save_config_raw(raw_text)
        self.remote_proto.load_config()
        print raw_text
    
    def handle_proto_reload(self):
        config_text = self.remote_proto.load_config_raw()
        self.text_proto_edit.setPlainText(config_text)
    
class ProtocolsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, remote_proto, parent=None):
        super(ProtocolsTableModel, self).__init__(parent)
    
        self.columns = {
                         0: "Protocol Friendly Name",
                         1: "Protocol Name",
                         2: "Port"
                        }

        self.remote_proto = remote_proto

        
    def refresh_interfaces(self):
        self.emit_data_changed()
             
    def save_protocols(self):
        pass
    
    def emit_data_changed(self):
        top_left = self.createIndex(0, 0)
        bottom_right = self.createIndex(1, 
                                        1)
        self.dataChanged.emit(top_left, bottom_right)  
             
    ## Required methods to subclass QAbstractTableModel    
    def rowCount(self, parent):
        return self.remote_proto.num_protos()
    
    def flags(self, index):
        toggled_flags = QtCore.Qt.NoItemFlags
        #toggled_flags |= QtCore.Qt.ItemIsEnabled
        #toggled_flags |= QtCore.Qt.ItemIsUserCheckable

        return toggled_flags
    
    def columnCount(self, parent):
        return len(self.columns)
    
    def setData(self, index, value, role):        
        # Emit dataChanged signal
        self.emit_data_changed()
        return True
        
    def data(self, index, role):
        
        # Displaying Data
        if role == QtCore.Qt.DisplayRole:            
            return QtCore.QVariant()

        # Editing Data (Not Needed)
        if role == QtCore.Qt.EditRole:
            pass
         
        # Align text   
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
         
        # Return internally managed checkbox state   
        if role == QtCore.Qt.CheckStateRole: 
            pass

        return QtCore.QVariant()
    ## Required methods to subclass QAbstractTableModel
    
    ## Optional methods for subclass of QAbstractTableModel 
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(20, 20)
        
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section > -1 and section < len(self.columns):
                    return self.columns[section]
    ## Optional methods for subclass of QAbstractTableModel  