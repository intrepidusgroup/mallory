from PyQt4 import QtGui, QtCore, Qt
import Pyro.core

from protocol import http, sslproto

class ProtocolsGui(object):
    """
    Controller and model for the protocol management GUI
    """
    def __init__(self, protocols_table, btn_reload, btn_apply, 
                 text_proto_edit, splitter_proto):
        self.protocols_table_view = protocols_table                
        self.btn_reload = btn_reload
        self.btn_apply = btn_apply
        self.text_proto_edit = text_proto_edit
        self.splitter_proto = splitter_proto
        
        # Set initial splitter sizes        
        self.splitter_proto.setSizes([200, 100])
                
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
        
        # Resize for good measure
        self.resize_content_columns()

    def connect_handlers(self):
        self.btn_apply.clicked.connect(self.handle_proto_apply)
        self.btn_reload.clicked.connect(self.handle_proto_reload)
        
    def handle_proto_apply(self):
        raw_text = self.text_proto_edit.toPlainText()
        self.remote_proto.save_config_raw(raw_text)
        
        # Causes Mallory to reload protocols
        self.remote_proto.load_config()
        
        # Update the model
        self.protocols_model.refresh_protocols()
        
        # Resize columns
        self.resize_content_columns()
        
    def resize_content_columns(self):
        self.protocols_table_view.resizeColumnsToContents() 
    
    def handle_proto_reload(self):
        config_text = self.remote_proto.load_config_raw()
        self.text_proto_edit.setPlainText(config_text)
    
PROTO_FRIENDLY = 0
PROTO_NAME = 1
PROTO_PORT = 2
PROTO_DEBUG = 3

class ProtocolsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, remote_proto, parent=None):
        super(ProtocolsTableModel, self).__init__(parent)
    
        self.columns = {
                         0: "Friendly Name", 
                         1: "Protocol Name",
                         2: "Port",
                         3: "Debuggable"
                        }

        self.remote_proto = remote_proto
        self.protocols = self.remote_proto.get_protocols()

        
    def refresh_protocols(self):
        prev_proto_count = len(self.protocols)
        self.protocols = self.remote_proto.get_protocols()
        new_proto_count = len(self.protocols)
        
        if new_proto_count > prev_proto_count:
            num_new_rows = new_proto_count - prev_proto_count
            self.insertRows(prev_proto_count, num_new_rows, 
                                QtCore.QModelIndex(), "")
        if new_proto_count < prev_proto_count:
            num_deleted_rows = prev_proto_count - new_proto_count
            del_start = prev_proto_count - num_deleted_rows
            
            if del_start != 0:
                del_start = del_start - 1
                
            self.removeRows(del_start, num_deleted_rows-1, 
                            QtCore.QModelIndex())
            
            
        self.emit_data_changed()
           
    def save_protocols(self):
        pass
    
    def emit_data_changed(self):
        top_left = self.createIndex(0, 0)
        bottom_right = self.createIndex(len(self.columns.keys()), 
                                        len(self.protocols))
        self.dataChanged.emit(top_left, bottom_right)  
             
    def insertRows(self, position, numrows, index, event):    
        self.beginInsertRows(QtCore.QModelIndex(), position, position+numrows-1)
        self.endInsertRows()
    
    def removeRows(self, row, count, index):
        first_row = row
        last_row = row+count
        self.beginRemoveRows(index, first_row, last_row)
        self.endRemoveRows()
                     
    ## Required methods to subclass QAbstractTableModel    
    def rowCount(self, parent):
        return len(self.protocols)
    
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
        
        # Hack to make content fitting look nice
        spacing = "        "
        
        # Displaying Data
        if role == QtCore.Qt.DisplayRole:
            num_cols = len(self.columns)
            
            proto = self.protocols[index.row()]
            
#            for proto in self.protocols:
#                print "Hmmn: %s, %s" % (proto, proto.__dict__)
            
            if index.column() > num_cols or index.column() < 0:
                return QtCore.QVariant()
            
            if index.column() == PROTO_FRIENDLY:
                x = self.protocols[index.row()]
                 
                return spacing + proto.friendly_name + spacing
            
            if index.column() == PROTO_NAME:
                proto_module = proto.__class__.__module__
                proto_name = proto.__class__.__name__
                
                # Extra spaces are hack to add proper spacing
                
                
                proto_str = spacing + proto_module + "." + proto_name + spacing
                
                return proto_str
            
            if index.column() == PROTO_PORT:
                return str(proto.serverPort)
            
            if index.column() == PROTO_DEBUG:
                debuggable = spacing + "No" + spacing
                
                if proto.__class__ == "TcpProtocol":
                    debuggable = spacing + "Yes" + spacing
                
                return debuggable
            
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