from PyQt4 import QtGui, QtCore, Qt
import TextViewDialogUi

try:
    from PyQt4 import QtSql
    NoQtSql = False
except:
    NoQtSql = True
    

from protocol import http, sslproto


FLOWS_QUERY = """
select c.connCount, c.serverIp, c.serverPort, c.clientIp, c.clientPort, 
    f.direction, f.timestamp, substr(buffer, 0, 32) as buffer
from connections c
inner join flows f ON f.conncount = c.conncount        
"""
        
MISSING_DEPS_TEXT = """You are missing QtSql (Ubuntu package python-qt4-sql) 
or QtSqlite (Ubuntu package libqt4-sql-sqlite) and maybe both.")

Database View Functionality Is Disabled"""

class DbGui(object):
    """
    Quick and dirty database GUI
    
    This is an expert interface. But, it is here for whatever it is worth.
    
    """
    def __init__(self, table_dbview, btn_exec_sql, btn_set_flows, text_db_sql,
                 splitter_db):
        self.table_dbview = table_dbview
        self.btn_exec_sql = btn_exec_sql
        self.btn_set_flows = btn_set_flows
        self.text_db_sql = text_db_sql
        self.splitter_db = splitter_db        
        self.current_model = None
        self.bufferview = BufferView(self)
        
        
         # Set initial splitter sizes        
        self.splitter_db.setSizes([200, 100])
        
        try:
            self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
            NoSqlite = False
        except:
            NoSqlite = True
            
        if NoQtSql or NoSqlite:
            warn = QtGui.QMessageBox.Warning 
            title = "Missing dependencies"
            text = MISSING_DEPS_TEXT
            self.msgbox = QtGui.QMessageBox(warn, title, text)
            self.msgbox.show()             
            return
        
        self.connect_handlers()
                
        self.db.setDatabaseName("../db/trafficdb")
        open = self.db.open()
        
    def connect_handlers(self):
        self.btn_exec_sql.clicked.connect(self.handle_exec_sql_clicked)
        self.btn_set_flows.clicked.connect(self.handle_set_flows_clicked)
        self.table_dbview.doubleClicked.connect(self.handle_row_double_clicked)
            
    def handle_exec_sql_clicked(self):
        sql_str = self.text_db_sql.toPlainText()
        model = QtSql.QSqlQueryModel()
        model.setQuery(sql_str)
        self.current_model = model
        self.table_dbview.setModel(model)
        
    def handle_set_flows_clicked(self):
        self.text_db_sql.setPlainText(FLOWS_QUERY)
        
    def handle_row_double_clicked(self, index):
        row = index.row()
        record = self.current_model.record(row)
        conn_count = record.value("conncount").toInt()
             
        buffers = []   
        #.toInt() returns a tuple
        conn_count = conn_count[0]
        query_str = "select buffer from flows where conncount = %d" % (conn_count)
        query = QtSql.QSqlQuery(self.db)
        query.exec_(query_str)
        
        while query.next():
            buffers.append(query.record().value("buffer").toString())
        
        big_buffers_str = ""
        for buffer in buffers:
            big_buffers_str += buffer + "\n\n\n-----\n\n\n"

        self.bufferview.setText(big_buffers_str)
        self.bufferview.show()
            
class BufferView(QtGui.QDialog):
    """
    This class creates a dialog that is used to capture and then insert a Hex or
    Text string into the data being edited.
    """
    def __init__(self, hexedit):
        QtGui.QDialog.__init__(self)
        self.dialog = TextViewDialogUi.Ui_Dialog()
        self.dialog.setupUi(self)
        
    def setText(self, text):
        self.dialog.textview.setPlainText(text)
        

        
    


