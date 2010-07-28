class Plugin ():
    """
    This is the base class for all plugins. Note that all plugins should assign
    a I{self.persistent} value. This I{self.persistent} value will be 0 if a plugin
    does not need to run a separate thread and 1 if it does.
    
    Note that plugs with a I{self.persistent} value of 1 needs to implement a
    I{self.runp} method. 
    
    All plugs need to implement a I{self.do} method to deal with hook points from
    a specific protocols hook points. 
    """
    def __init__(self):
        self.persistent = 0
        
    def do(self, **kwargs):
        """
        The I{self.do} function expects name value list that hold an event and data element.
        kwargs['event'] should return an identifier for the plugin to understand which hook
        was triggered to send the plugin event. kwargs['data'] should return the piece of data
        that the plugins will need to operate on/with. 
        
        A plugin must return the kwargs['data'] object upon completion. The objection may be
        unchanged or may be edited based on the plugins logic
        """
        pass
    
    def runp(self) :
        """
        If a plugin is persistent this method will be initiated in its own thread upon plugin
        initialization. This can be used for plugins that need to maintain state between calls or
        run some constant piece of code.For example, a plugin that needs to save all cookie 
        information during a mallory session and present it to a web browser would use this
        method.
        """
        pass