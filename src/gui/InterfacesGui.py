from PyQt4 import QtGui, QtCore, Qt

import config_if

COLUMN_IFS = 0
COLUMN_MITM = 1
COLUMN_OUT = 2

"""
TODO: Centering checkboxes requires a custom Item Delegate. We will avoid this
problem for now. Here are the relevant references:

http://developer.qt.nokia.com/faq/answer/how_can_i_align_the_checkboxes_in_a_view
http://lists.trolltech.com/qt-interest/2006-06/msg00476.html
http://stackoverflow.com/questions/4403704/qt-qtableview-alignment-of-checkbox-when-using-isusercheckable
http://stackoverflow.com/questions/1744348/embedding-a-control-in-a-qtableview

"""

# TODO: Add IP address coumn
# TODO: Load existing iptables config? (maybe)

class InterfacesGui(object):
    def __init__(self, interfaces_table, btnsaveifcfg, btnrefreshifaces):
        self.interfaces_table_view = interfaces_table
        self.interfaces_model = InterfacesTableModel()
        self.interfaces_table_view.setModel(self.interfaces_model)
        self.btnsaveifcfg = btnsaveifcfg
        self.btnrefreshifaces = btnrefreshifaces
        
        # Set column widths
        for column in self.interfaces_model.columns.keys():
            self.interfaces_table_view.setColumnWidth(column, 150)
      
        self.connect_handlers()
        
    def connect_handlers(self):
        self.btnsaveifcfg.clicked.connect(self.handle_saveconfig)
        self.btnrefreshifaces.clicked.connect(self.handle_refreshifaces)
    
    def handle_saveconfig(self):
        print "Handling save confg"
        self.interfaces_model.save_config()
     
    def handle_refreshifaces(self):
        print "Handling interfaces refresh"
        self.interfaces_model.refresh_interfaces()
        self.interfaces_model.reset()

   
    def resize_content_columns(self):
        self.interfaces_table_view.resizeColumnsToContents()      
        
class InterfacesTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(InterfacesTableModel, self).__init__(parent)
    
        self.columns = {
                         0: "Interface Name",
                         1: "Perform MiTM",
                         2: "Outbound Interface"
                        }
           
        # TODO: Make this a remote mallory server object     
        self.if_cfg = config_if.ConfigInterfaces()
        
        # Get interfaces, sort them, save them in if_cfg
        self.refresh_interfaces()
            
        self.checked = True
    
    
    def refresh_interfaces(self):
        ni = config_if.NetworkInterfaces()
        ifs_list = ni.get_ifs().keys()
        ifs_list.sort()
        self.if_cfg.set_interfaces(ifs_list)
        self.emit_data_changed()
             
    def save_config(self):
        self.if_cfg.save()
    
    def emit_data_changed(self):
        top_left = self.createIndex(0, 0)
        bottom_right = self.createIndex(len(self.columns.keys()), 
                                        self.if_cfg.num_ifs())
        self.dataChanged.emit(top_left, bottom_right)  
             
    ## Required methods to subclass QAbstractTableModel    
    def rowCount(self, parent):
        return self.if_cfg.num_ifs()
    
    def flags(self, index):
        toggled_flags = QtCore.Qt.NoItemFlags
        toggled_flags |= QtCore.Qt.ItemIsEnabled

        if index.column() == COLUMN_MITM or index.column() == COLUMN_OUT:
            toggled_flags |= QtCore.Qt.ItemIsUserCheckable

        return toggled_flags
    
        #return 0
    
    def columnCount(self, parent):
        return len(self.columns)
    
    def setData(self, index, value, role):
        value_bool = value.toBool()
        column = index.column()
        row = index.row()
        
        if_name = self.if_cfg.get_if_for_idx(row)
        
        # Toggling MiTM
        if index.column() == COLUMN_MITM:
            if value_bool == False:
                self.if_cfg.set_mitm(if_name, False)
            else:
                self.if_cfg.set_mitm(if_name, True)
                
        # Toggling Outbound       
        if index.column() == COLUMN_OUT:
            if value_bool == False:
                self.if_cfg.set_outbound(if_name, False)
            else:
                self.if_cfg.set_outbound(if_name, True)
        
        # Emit dataChanged signal
        self.emit_data_changed()
        
        return True
        
    def data(self, index, role):
        
        # Displaying Data
        if role == QtCore.Qt.DisplayRole:
            # Sanity check
            if index.row() < 0 or index.row() > self.if_cfg.num_ifs():
                return QtCore.QVariant()
            
            if index.column() == COLUMN_IFS:
                return self.if_cfg.get_if_for_idx(index.row())
            
            if index.column() == COLUMN_MITM:
                return QtCore.QVariant()

        # Editing Data (Not Needed)
        if role == QtCore.Qt.EditRole:
            if index.column() == COLUMN_MITM:
                pass
         
        # Align text   
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
         
        # Return internally managed checkbox state   
        if role == QtCore.Qt.CheckStateRole: 
            if_name = self.if_cfg.get_if_for_idx(index.row())
            
            if index.column() == COLUMN_MITM:
                if self.if_cfg.is_mitm(if_name):
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
            
            if index.column() == COLUMN_OUT:
                if self.if_cfg.is_outbound(if_name):
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
                    

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
