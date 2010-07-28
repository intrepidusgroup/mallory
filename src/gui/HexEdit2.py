import sys
import random
import binascii

from PyQt4 import QtGui, QtCore
from HexEditUi import Ui_MainWindow

COLUMN_WIDTH = 25
BYTES_PER_ROW = 16

class HexGui(QtGui.QMainWindow):
           
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.main =  Ui_MainWindow()        
        self.app = None
        self.bdata = None
        self.ready = False

    def setupTable(self):    
        table = self.main.tableWidget    
                
        table.cellChanged.connect(self.handle_cellChanged)
                
        numcols = table.columnCount()
        for col in range(0, numcols):
            table.setColumnWidth(col, COLUMN_WIDTH)
        table.setColumnWidth(numcols-1, 256)
     
    def fixedWidthFont(self):
        f = QtGui.QFont("Courier")
        return f
    
    def loadData(self, data):       
        table = self.main.tableWidget
        #item = QtGui.QTableWidgetItem(binascii.hexlify(self.getBinaryData(1)))
        self.bdata  = self.getBinaryData(1024)
        print len(self.bdata)
        rows = (len(self.bdata)/BYTES_PER_ROW)+1
        table.setRowCount(rows)
        numcols = table.columnCount()
        
        datacnt = 0
        datalen = len(self.bdata)
        rowstr = ""
        
        for row in range(0, rows):            
            for column in range(0, BYTES_PER_ROW):
                if datacnt == datalen:
                    colsleft = BYTES_PER_ROW-column
                    for colleft in range(0, colsleft):
                        disabled = QtGui.QTableWidgetItem("")
                        disabled.setFlags(QtCore.Qt.ItemIsEnabled)
                        table.setItem(row, colleft+column, disabled)
                        #.setFlags(QtCore.Qt.ItemIsEnabled)
                    break                            
                rowstr += self.bdata[datacnt]
                colItem = QtGui.QTableWidgetItem(binascii.hexlify(self.bdata[datacnt]))            
                colItem.setFont(self.fixedWidthFont())
                table.setItem(row, column, colItem)
                
        
                datacnt += 1
            rowItem = QtGui.QTableWidgetItem(self.prettyPrint(rowstr))
            rowItem.setFont(self.fixedWidthFont())
            rowItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(row, table.columnCount()-1, rowItem)
            rowstr = ""
        
        
    def handle_cellChanged(self, row, col):
        if not self.ready:
            return
        
        if col >= BYTES_PER_ROW:
            return
        
        table = self.main.tableWidget

        validText = self.validateHex(table.item(row, col).text())    
        idx = self.getByteFromCoord(row,col)
        origText = binascii.hexlify(self.bdata[idx]).lower()
        
        print "ByteFromCoord: %s:%s:%d:%d"  % (origText,validText,idx, len(self.bdata))
        print origText, validText
        if binascii.unhexlify(origText).lower() != validText:
            text = validText
            table.item(row,col).setText(text)
            idx = self.getByteFromCoord(row, col)
            replbyte = binascii.unhexlify(text)
            print "Got bnum: %d" % (idx)
            
            start = self.getByteFromCoord(row, 0)
            end = self.getByteFromCoord(row, 16)
            print "row:%d col:%d start:%s end:%s bdata:%s" % (row, col, start, end, self.bdata[start:end])
            self.bdata = self.replOneByte(self.bdata, idx, replbyte)
            print "row:%d col:%d start:%s end:%s bdata:%s" % (row, col, start, end, self.bdata[start:end])
            #print "Start is: %d and end is %d" % (start, end)
            newtext = self.prettyPrint(self.bdata[start:end])
            table.item(row, 16).setText(newtext)

        print len(self.bdata), repr(self.bdata)
        #print "bdatalen: " + bdatalen + "" + str(len(self.bdata))
        print row, col
        
    def getCoordFromByte(self, bnum):
        row = bnum / BYTES_PER_ROW
        col = bnum % BYTES_PER_ROW
        return row, col
    
    def getByteFromCoord(self, row, col):
        return row * 16 + col
        
    def replOneByte(self, x, bnum, byte):
        print "IN STRING: " + x
        # Validate / clean up incoming parameters
        if bnum < 0:
            bnum = 0    
        if bnum >= len(x):
            bnum = len(x)-1    
        x = str(x)
         
        begin = x[0:bnum]
        repl = byte
        end =  x[bnum+1:]
        
        y =  begin + repl + end
           
        print "OUT STRING: " + y 
        return y
    
    def validateHex(self, hexin):
        hexin = str(hexin)
        
        if(len(hexin)) == 1:
            hexin = "0" + hexin
            
        if len(hexin) > 2 or len(hexin) == 0:
            hexin = "41"
            
        try:
            x = binascii.unhexlify(hexin)
        except:
            hexin = "41"
        
        return hexin
                                            
    def doStuff(self):
        table = self.main.tableWidget
        headerItem = QtGui.QTableWidgetItem()
        headerItem.setText("Yay")
        self.getBinaryData(128)
        
    def prettyPrint(self, str):
        prettystr = ""
        
        for byte in str:
            bnum = ord(byte)
            
            if bnum < 33 or bnum > 127:
                prettystr += "."
            else:
                prettystr += byte
                
        return prettystr              
                
    def getBinaryData(self, nbytes):
        data = ""
        for curbyte in range(0, nbytes):
            data += chr(random.randrange(33, 127))
            
        print "Generated: " + str(len(data)) + "bytes of data||| " + data
        return data
        

def main():
    app = QtGui.QApplication(sys.argv)
    window = HexGui()    
    window.app = app    
    window.main.setupUi(window)        
    window.show()
    window.setupTable()
    #window.doStuff()
    window.loadData("blargh")
    #window.modOneByte(448, "41")
    window.ready = True
    sys.exit(app.exec_()) 
          
if __name__ == "__main__":
    main()
