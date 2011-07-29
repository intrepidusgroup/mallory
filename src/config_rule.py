import ConfigParser
import protocol
import sets
import logging
import Pyro.core
import observer
import rule



class ConfigRules(observer.Subject, Pyro.core.ObjBase):
    """
    Rule configuration is to manage the RPC interface to getting and setting
    rules as well as the local activities of loading saved rule configuration.
    
    """
    def __init__(self):
        observer.Subject.__init__(self)
        Pyro.core.ObjBase.__init__(self)
        
        self.log = logging.getLogger("mallorymain")
        self.config_path = "rules.ini"
        self.log.info("ConfigRules.init: LOADING RULES.")
        self.rules = self.load_config()
        
        
    def load_config_raw(self):
        """
        Load the raw configuration file from disk.
        
        @return: string - the configuration file loaded from persistent storage
        """
        f = open(self.config_path, "r")
        config_raw = f.read()
        f.close()
        
        return config_raw
    
    
    def load_muck_actions(self, _rule):
        """
        Load muck actions for a given rule.
        
        @param _rule: The rule name to load parameters for
        @type _rule: string 
        """
        rule_keys = _rule.keys()
        
        mucks = []
        for rule_key in rule_keys:
            if rule_key.find("muck_") == 0:
                mucks.append(_rule[rule_key])

        muck_action = rule.Muck()
        
        try:
            muck_action = rule.Muck(mucks)
        except:
            print self.log.info( ("ConfigRules:load_muck_actions "
                                  "- bad config syntax"))

        return muck_action
    
                
    def load_config(self):
        """
        Load a configuration from disk.
        
        @return: List of L{rule.Rule} objects
        """
        cp = ConfigParser.ConfigParser()
        cp.read(self.config_path)
        config_rules = cp.sections()
        
        rules = []
        
        rule_dict = {}
        
        # Loop over each rule (config section)
        for _rule in config_rules:
            rule_dict = {}
            
            # Gather rule items
            rule_items = cp.items(_rule)
            for item in rule_items:
                rule_dict[item[0]] = item[1]
                
            # Set the rule name
            rule_dict["name"] = _rule
            
            rules.append(rule_dict)
        
        # Translate into real rule objects
        real_rules = []
        
        _rule = {}
        
        for _rule in rules:
            rule_action = rule.Nothing()
                        
            if "action" in _rule:
                rule_act_str = _rule["action"]
                
                self.log.info("ConfigRules.load_config: Rule Action String "
                              "is:%s" % (rule_act_str))
                
                if rule_act_str == "Nothing":
                    rule_action = rule.Nothing()
                elif rule_act_str == "Debug":
                    rule_action = rule.Debug()
                elif rule_act_str == "Muck":
                    rule_action = self.load_muck_actions(_rule)
                elif rule_act_str == "Fuzz":
                    rule_action = rule.Fuzz()
                else:
                    rule_action = rule.Nothing()
                    
                _rule["action"] = rule_action

            
            real_rule = rule.Rule("").fromdict(_rule)
            
            real_rules.append(real_rule)
            
        self.rules = real_rules
        
        return real_rules
            
            
                
    
    def get_rules(self):
        """
        Get and return the current ruleset that is being enforced
        
        @return: array of L{rule.Rule} objects
        """     
        if self.rules is None:
            return []
        
        for rule in self.rules:
            self.log.debug("ConfigRules.getrules: %s" % (str(rule)))

        self.log.debug("ConfigRules.getrules: client requested rules -  %s" % (self.rules))
        
        return self.rules
    
    def update_rules(self, rule_array):
        """
        Update the current array of rule objects
        
        @param rulearray: The array of rule objects to replace the current one.
        @type rulearray: array of L{rule.Rule}
        """
        self.rules = rule_array
        
        for rule in self.rules:
            self.log.debug("ConfigRules.updaterules: %s" % (str(rule)))
#            if rule.action.name == "muck":
#                self.log.debug("Debugger.updaterules: %s" % (rule.action.mucks))
#                for muck in rule.action.mucks:
#                    self.log.debug("Debugger.updaterules.muck: %s" %(binascii.hexlify(muck)))
                
            
        #self.log.debug("ConfigRules.update_rules: %s" % (rule_array))
        
        self.notify(event="updaterules", rules=rule_array)
        
        return ""             

        
if __name__ == "__main__":
    cr = ConfigRules()
