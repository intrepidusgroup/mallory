import binascii
import HexDialogInsertUi

from PyQt4 import QtGui, QtCore

# Width in pixels
COLUMN_WIDTH = 25

BYTES_PER_ROW = 16

class HexEdit(object):
    """
    The table must be created and placed into a UI layout. This class provides a
    hex editor via a QTableWidget. It requires a QTableWidget and provides all
    of the functions required to set the table up.
    """
    def __init__(self, table, app, status):
        self.table = table        
        self.app = app
        # This is the "model" / data for this class: a binary sequence.
        self.bdata = None
        self.ready = False
        self.status = status
        self.insertbytes = InsertBytes(self)

    def setupTable(self):
        table = self.table    
        table.setColumnCount(BYTES_PER_ROW+1)
        table.cellChanged.connect(self.handle_cellChanged)
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.handle_menu)
        table.currentCellChanged.connect(self.handle_currentCellChanged)
        table.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
                        
        numcols = table.columnCount()
        for col in range(0, numcols):
            table.setColumnWidth(col, COLUMN_WIDTH)
        table.setColumnWidth(numcols-1, 256)
        
        headerlbls = ["%x"%(s) for s in range(0,16)]
        headerlbls.append("ASCII")
        table.setHorizontalHeaderLabels(headerlbls)
        
             
    def fixedWidthFont(self):
        f = QtGui.QFont("Courier")
        return f
    
    def loadData(self, data):
        """
        Load the binary data to be edited
        """
        table = self.table
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
                
        #item = QtGui.QTableWidgetItem(binascii.hexlify(self.getBinaryData(1)))
        self.bdata = data
        rows = (len(self.bdata)/BYTES_PER_ROW)+1
        table.setRowCount(rows)
        numcols = table.columnCount()
        
        rowlbls = ["%x" % (x*BYTES_PER_ROW) for x in range(0,rows)]
        table.setVerticalHeaderLabels(rowlbls)
        datacnt = 0
        datalen = len(self.bdata)
        rowstr = ""
        
        for row in range(0, rows):            
            for column in range(0, BYTES_PER_ROW):
                if datacnt == datalen:
                    colsleft = BYTES_PER_ROW-column
                    
                    # Used up all bytes in data. Disable remaining cells.
                    for colleft in range(0, colsleft):
                        disabled = QtGui.QTableWidgetItem("")
                        disabled.setFlags(QtCore.Qt.ItemIsEnabled)
                        table.setItem(row, colleft+column, disabled)
                        #.setFlags(QtCore.Qt.ItemIsEnabled)
                    break                            
                rowstr += self.bdata[datacnt]
                colItem = QtGui.QTableWidgetItem(
                              binascii.hexlify(self.bdata[datacnt]))            
                colItem.setFont(self.fixedWidthFont())
                table.setItem(row, column, colItem)
                
        
                datacnt += 1
            rowItem = QtGui.QTableWidgetItem(self.prettyPrint(rowstr))
            rowItem.setFont(self.fixedWidthFont())
            rowItem.setFlags(QtCore.Qt.ItemIsEnabled)
            table.setItem(row, table.columnCount()-1, rowItem)
            rowstr = ""
        
    def handle_menu(self, point):
        table = self.table
        menu = QtGui.QMenu(table)
        copyHexAllBytes = menu.addAction("Copy (hex) - All")
        copyTextAllBytes = menu.addAction("Copy (text) - All")
        insertBytes = menu.addAction("Insert Bytes")
        deleteBytes = menu.addAction("Delete Bytes")
        pasteHexAllBytes = menu.addAction("Paste (hex) - Replace All")
        pasteTextAllBytes = menu.addAction("Paste (text) - Replace All")
        #pasteSelectedBytes = menu.addAction("Paste - Replace Selected")
        action = menu.exec_(table.mapToGlobal(point))
                
        clipboard = self.app.clipboard()
             
        if action == copyHexAllBytes:
            clipboard.setText(binascii.hexlify(self.bdata))
        if action == copyTextAllBytes:
            clipboard.setText(self.bdata)
        if action == pasteHexAllBytes:
            cliptext = str(clipboard.text())
            try:
                cliptext = binascii.unhexlify(cliptext)
            except:
                # Need to refactor this. Repeated code.
                warn = QtGui.QMessageBox.Warning 
                title = "Error in hex string."
                text = "Error in hex string. Valid string: 'ff ab 34 de ad " \
                "be' or 'd989defb'. There must be an even number of bytes " \
                "and the characters must be 0-9, a-f A-F" 
                self.msgbox = QtGui.QMessageBox(warn, title, text)
                self.msgbox.show()
                return
                
            self.loadData(cliptext)
            
        if action == pasteTextAllBytes:
            cliptext = str(clipboard.text())
            self.loadData(cliptext)             
                        
        if action == insertBytes:
            self.insertbytes.point = point
            
            # Dialog will trigger actual byte insertion routines
            self.insertbytes.show()
            
        if action == deleteBytes:
            selections = table.selectedIndexes()
            delbytes = []
            for sel in selections:
                delbyte = self.getByteFromCoord(sel.row(), sel.column())
                delbytes.append(delbyte)
            delbytes.sort()
            
            delranges = []
            
            # O(n) algorithm to get contiguous ranges from delbytes
            # precondition: no duplicates. list must be sorted.
            cnt = 0
            low = delbytes[0]
            for byte in delbytes:                
                # Make sure to get the last byte
                if cnt+1 == len(delbytes):
                    delranges.append([low,byte])
                    break
                # If the next byte diff is more than 1, create a range
                else:
                    nextbyte = delbytes[cnt+1]
                    diff = nextbyte-byte
                    if diff > 1:
                        delranges.append([low,byte])
                        low = nextbyte         
                cnt += 1
            
            # Delete the bytes
            newdata = self.bdata  
            deletedbytes = 0          
            print delranges
            for range in delranges:
                start = range[0] - deletedbytes
                end = range[1] - deletedbytes
                newdata = newdata[0:start] + newdata[end+1:]                
                # Track deleted bytes to adjust deletion indicies
                deletedbytes += range[1]+1 - range[0]
                #print "Newdata:%s,start:%d,end:%d" % (newdata, start, end)

            self.loadData(newdata)
                
    def handle_cellChanged(self, row, col):
        """
        Handle with the edit event from the user. Edit a specific row and
        column and make the appropriate updates. This should be connected
        to the cellChanged slot of the QTableWidget
        """
        if not self.ready:
            return
        
        if col >= BYTES_PER_ROW:
            return
        
        table = self.table
        
        validText = self.validateHex(table.item(row, col).text())    
        idx = self.getByteFromCoord(row,col)

        if idx > len(self.bdata)-1:
            return
        
        origText = binascii.hexlify(self.bdata[idx]).lower()
        
        #print "ByteFromCoord: %s:%s:%d:%d"  % (origText,validText,idx,len(self.bdata))
        #print origText, validText
        
        # If the data has changed, update the view and the model(bdata)
        if binascii.unhexlify(origText).lower() != validText:
            text = validText
            table.item(row,col).setText(text)
            idx = self.getByteFromCoord(row, col)
            replbyte = binascii.unhexlify(text)
            #print "Got bnum: %d" % (idx)

            
            start = self.getByteFromCoord(row, 0)
            end = self.getByteFromCoord(row, 16)
            #print "row:%d col:%d start:%s end:%s bdata:%s" % (row, col, start, end, self.bdata[start:end])
            self.bdata = self.replOneByte(self.bdata, idx, replbyte)
            #print "row:%d col:%d start:%s end:%s bdata:%s" % (row, col, start, end, self.bdata[start:end])
            #print "Start is: %d and end is %d" % (start, end)
            newtext = self.prettyPrint(self.bdata[start:end])
            if table.item(row, BYTES_PER_ROW):
                table.item(row, BYTES_PER_ROW).setText(newtext)

        #print "bdatalen: " + bdatalen + "" + str(len(self.bdata))
        
    def handle_currentCellChanged(self, row, col, oldrow, oldcol):
        # If there is not a valid QStatusBar in self.status don't bother
        # updating the status. This widget may get used in places where it can't
        # update the status bar
        if not self.status:
            return
        if self.status.__class__ != QtGui.QStatusBar:
            return
        
        nbyte = self.getByteFromCoord(row, col)
        
#        bytesback = nbyte-3
#        bytesforward = nbyte+3
#        if bytesback < 0:
#            bytesback = 0
#        if bytesforward > len(self.bdata):
#            bytesforward = len(self.bdata)
#            
#        statusstr = repr(self.bdata[nbyte-bytesback:nbyte])  
#        statusstr += "[%s]" % (repr(self.bdata[nbyte]))
#        statusstr += repr(self.bdata[nbyte+1:nbyte+bytesforward])
        
        data = self.bdata
        dlen = len(self.bdata)
        
        if nbyte >= dlen:
            self.status.showMessage("")
            return
        
        # Display a few bytes of context and highlight the current byte
        statusstr = "Current Hex Edit Byte [0x%x,%d]: " % (nbyte,nbyte)
        statusstr += "".join([data[x] for x in range(nbyte-2, nbyte) \
                             if x >= 0 and x < dlen])
        statusstr += " >>%s<< " % (data[nbyte])
        statusstr += "".join([data[x] for x in range(nbyte+1, nbyte+3) \
                             if x >= 0 and x < dlen])
        
        self.status.showMessage(repr(statusstr).strip("'"))

            
    def getCoordFromByte(self, bnum):
        """
        Given a byte number (index) in the edited string return the row and
        column for the string
        """
        row = bnum / BYTES_PER_ROW
        col = bnum % BYTES_PER_ROW
        return row, col
    
    def getByteFromCoord(self, row, col):
        """
        Get a byte index from a row and column
        """
        return row * BYTES_PER_ROW + col
        
    def replOneByte(self, x, bnum, byte):
        """
        Replace one byte (with potentially many new bytes)
        """
        # Sanity checks
        if bnum < 0:
            bnum = 0    
        if bnum >= len(x):
            bnum = len(x)-1    
        x = str(x)
        
        # Mangle string
        begin = x[0:bnum]
        repl = byte
        end =  x[bnum+1:]
            
        return begin + repl + end
    
    def insertBytes(self, str, bnum, bytes):
        """
        insert bytes from variable bytes into str str starting at byte number
        bnum
        """
        return str[0:bnum] + bytes + str[bnum:]
    
    def validateHex(self, hexin):
        """
        Validate that the string passed in via the hexin parameter is a valid
        two digit hex string that can be converted by binascii.unhexlify
        
        If it is not replace it with 0x41 (A) (just cause) 
        """
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
                                                
    def prettyPrint(self, str):
        """
        Print a string with all binary data printed as a . character. 
        """
        prettystr = ""
        
        # TODO: examine potential for a list comprehension here 
        for byte in str:
            bnum = ord(byte)
            
            if bnum < 33 or bnum > 127:
                prettystr += "."
            else:
                prettystr += byte
                
        return prettystr              
          
    def getData(self):
        """Return edited binary data"""
        return self.bdata
    def getRandomBinaryData(self, nbytes):
        """
        Get some random printable binary data
        """
        
        data = ""
        for curbyte in range(0, nbytes):
            data += chr(random.randrange(33, 127))
            
        #print "Generated: " + str(len(data)) + "bytes of data||| " + data
        return data


class InsertBytes(QtGui.QDialog):
    """
    This class creates a dialog that is used to capture and then insert a Hex or
    Text string into the data being edited.
    """
    def __init__(self, hexedit):
        QtGui.QDialog.__init__(self)
        self.dialog = HexDialogInsertUi.Ui_HexDialogInsert()
        self.dialog.setupUi(self)
        self.connecthandlers()
        self.hexedit = hexedit # tightly couples to hexedit
        self.point = None
        
    def connecthandlers(self):
        self.dialog.buttonBox.accepted.connect(self.handle_accept)
        self.dialog.buttonBox.rejected.connect(self.handle_reject)
        
    def handle_accept(self):
        if not self.point:
            self.hide()
            return
        
        insbytes = ""
        if self.dialog.radioText.isChecked():
            insbytes = str(self.dialog.lineText.displayText())
            
        if self.dialog.radioHex.isChecked():
            print "Doing hex thing"
            insbytes = str(self.dialog.lineHex.displayText())
            try:
                insbytes = binascii.unhexlify(insbytes)
            except:
                warn = QtGui.QMessageBox.Warning 
                title = "Error in hex string."
                text = "Error in hex string. Valid string: 'ff ab 34 de ad " \
                "be' or 'd989defb'. There must be an even number of bytes " \
                "and the characters must be 0-9, a-f A-F" 
                self.msgbox = QtGui.QMessageBox(warn, title, text)
                self.msgbox.show()
                return
                    
        # save changes to table
        table = self.hexedit.table
        
        # Get byte index of insertion point
        insertmodel = table.indexAt(self.point)
        row = insertmodel.row()
        col = insertmodel.column()
        nbyte = self.hexedit.getByteFromCoord(row, col)
        
        # Insert the byte        
        data = self.hexedit.getData()        
        newstr = data[0:nbyte] + insbytes + data[nbyte:]
        
        # Load the data and redraw the gui        
        self.hexedit.loadData(newstr)
        
        print row,col
                
        # TODO: Save changes
        self.hide()
        
    def handle_reject(self):
        self.hide()
