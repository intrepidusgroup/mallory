import rule
import base64
import pickle
import sys
import muckpipe
import binascii

from PyQt4 import QtGui, QtCore

RULEUP = -1
RULEDOWN = 1

class RuleEdit(object):
    def __init__(self, main, rulemod):
        self.main = main
        self.rulemod = rulemod
    
    def get_enc_rulepickle(self):
        return self.rulemod.getRules()
    
    def handle_ruleadd(self):
        rules = self.main.listrules
        row = 0 
        if len(rules.selectedIndexes())>0:
            selected = rules.selectedIndexes()[0]        
            row = selected.row()

        newrule = rule.Rule(name="new_rule")   
        self.rulemod.addRuleBefore(row, newrule)
        
        
    def handle_ruledel(self):
        rules = self.main.listrules
        selected = rules.selectedIndexes()[0]
        selrow = selected.row()
        self.rulemod.delRule(selrow)
            
    def handle_ruleupdown(self, dir):
        rules = self.main.listrules
        selected = rules.selectedIndexes()[0]
        selrow = selected.row()
       
        if dir == RULEDOWN:
            if selrow < 0 or selrow >= self.rulemod.rowCount()-1:
                return
        elif dir == RULEUP:
            if selrow < 1 or selrow >= self.rulemod.rowCount():
                return
        else:
            return
        
        rl = self.rulemod.getRules()
 
        rl[selrow], rl[selrow+dir] = rl[selrow+dir], rl[selrow]
        
        self.rulemod.setRules(rl)
        
        self.rulemod.reset()
        
        index = self.rulemod.createIndex(selrow+dir, 0)
        
        self.main.listrules.setCurrentIndex(index)
               
    def handle_ruledown(self):
        self.handle_ruleupdown(RULEDOWN)
        
    def handle_ruleup(self):
        self.handle_ruleupdown(RULEUP)
        
    def handle_ruleactivated(self, index):
        rule = self.rulemod.getRule(int(index.row()))
        
        print "Rule: %s" % (str(rule))
        self.main.linename.setText(rule.name)
        
        if rule.direction == "s2c":
            self.main.radio_dir_s2c.toggle()
        elif rule.direction == "c2s":
            self.main.radio_dir_c2s.toggle()
        else:
            self.main.radio_dir_both.toggle()
    
        if rule.addr != "":
            self.main.lineaddr.setText(rule.addr)
        else:
            self.main.lineaddr.setText("")
        
        self.main.lineport.setText(rule.port)
        # temporary placement until payload is added
        try:
           self.main.linepayload.setText(rule.payload.encode("string-escape"))
        except:
           pass
       
        if rule.passthru == True:
            self.main.radio_passthru_yes.toggle()
        else:
            self.main.radio_passthru_no.toggle()
            
        self.main.textruleobj.setPlainText("")
        if rule.action.name == "debug":
            self.main.radio_type_debug.toggle()
        elif rule.action.name == "muck":            
            self.main.radio_type_muck.toggle()
            mucks = rule.action.mucks
            muckstr = "\n".join(mucks)
            self.main.textruleobj.setPlainText(muckstr.encode("string-escape"))            
        else:
            self.main.radio_type_nothing.toggle()
                
        print "Activated %d" % (int(index.row()))         
        
    def handle_saverule(self):
        newrule = self.rulefromform()
        
        if newrule is None:
            return
        
        rules = self.main.listrules
        selected = rules.selectedIndexes()[0]
        self.rulemod.setRule(int(selected.row()), newrule)
        self.rulemod.reset()
         
        
        return self.rulemod.getRules()
    
    def rulefromform(self):
        name = str(self.main.linename.text())
        direction = ""        
        if self.main.radio_dir_s2c.isChecked():
            direction = "s2c"
        elif self.main.radio_dir_c2s.isChecked():
            direction = "c2s"
                
        addr = self.main.lineaddr.text()
        # Will have three dots when address is empty due to mask
        # Not a strict check, but it lets wildcard rules exist
        if addr == "...":
            addr = ""
        
        port = self.main.lineport.text()
        
        payload = "" # temporary placement until guis element  is added
                
        try:
           payload = str(self.main.linepayload.text()).decode("string-escape")
        except:
           pass
       
        passthru = False
        if self.main.radio_passthru_yes.isChecked():
            passthru = True
            
        action = rule.Nothing()
        if self.main.radio_type_debug.isChecked():
            action = rule.Debug()
            print "RuleEdit.rulefromform: creating debug rule"   
        elif self.main.radio_type_muck.isChecked():
            muckstr = str(self.main.textruleobj.toPlainText())
            muckarr = muckstr.split("\n")                
            muckarr = [i.decode("string-escape") for i in muckarr]            
            action = rule.Muck(muckarr)
            
            try:
                mp = muckpipe.MuckPipe("").fromlist(action.mucks)
                mp.data = "dark and empty"
                mp.muck()
            except:
                warn = QtGui.QMessageBox.Warning 
                title = "Invalid Muckpipe Specification"
                text = "Please check the syntax of your Muck(s). " \
                "For more information on muck rule formatting please " \
                "hover over the 'Muck' label in this form"                
                self.msgbox = QtGui.QMessageBox(warn, title, text)
                self.msgbox.show()
                print sys.exc_info()
                return None                    
        
        newrule = rule.Rule("").fromdict({
            "name":name,
            "passthru":passthru,
            "direction":direction,
            "addr":addr,
            "port":port,
            "action":action,
            "payload":payload
         })
             
        print "Newrule %s" % (newrule)
        return newrule

class RuleList(QtCore.QAbstractListModel):
    def __init__(self, rules = [], parent=None):
        super(RuleList, self).__init__(parent)
        self.rules = rules
    
    def setRule(self, index, rule):
        self.rules[index] = rule
        
    def setRules(self, rules):
        self.rules = rules
        
    def getRule(self, index):
        if index >= len(self.rules):
            return None
        return self.rules[index]
    
    def getRules(self):
        return self.rules
    
    def rowCount(self, parent = None):
        return len(self.rules)
    
    def addRuleBefore(self, index, rule):
        if index == 0:
            self.rules.insert(index, rule)
        elif index < 0 or index >= self.rowCount():
            return
        else:
            self.rules.insert(index, rule)
        self.reset()
        
    def delRule(self, index):
        if index < 0 or index >= self.rowCount():
            return
        
        del self.rules[index]        
        self.reset()
        
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole and index.isValid():
            return self.rules[int(index.row())].name         
