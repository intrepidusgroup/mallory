class PluginManagerBase ():
    def __init__(self):
        self.plugins = []

    def process (self, **kwargs):
        oldkwargs = kwargs
        try:
            for plugin in self.plugins:
                kwargs = plugin.do(**kwargs)
        except:
            kwargs = oldkwargs
        return kwargs.get('data',None)
    


