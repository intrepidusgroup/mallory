import ConfigParser
import protocol
import sets
import logging
import Pyro.core
import observer
import rule


class ConfigRules(observer.Subject, Pyro.core.ObjBase):
    def __init__(self):
        observer.Subject.__init__(self)
        Pyro.core.ObjBase.__init__(self)
        
        self.config_path = "rules.ini"
        self.load_config()
        
        
    def load_config_raw(self):
        f = open(self.config_path, "r")
        config_raw = f.read()
        f.close()
        
        return config_raw
    
    
    def load_muck_actions(self, _rule):
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
                
                print "Rule Action String is:%s" % (rule_act_str)
                
                if rule_act_str == "Nothing":
                    rule_action = rule.Nothing()
                elif rule_act_str == "Debug":
                    rule_action = rule.Debug()
                elif rule_act_str == "Muck":
                    rule_action = self.load_muck_actions(_rule)
                else:
                    rule_action = rule.Nothing()
                    
                _rule["action"] = rule_action

            
            real_rule = rule.Rule("").fromdict(_rule)
            
            real_rules.append(real_rule)
            
        print real_rules
        
        for asdfasdf in real_rules:
            print asdfasdf
            
            
                
        
        
if __name__ == "__main__":
    cr = ConfigRules()
