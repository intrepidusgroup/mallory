class Subject(object):
    """This subject / main actor in the Observer pattern. This is not used just
    yet, but it should be in the future. Leaving it in for now."""
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, **kwargs):
        """Note that kwargs is used here for flexible arguments on notify"""
        for observer in self._observers:
            observer.update(self, **kwargs)