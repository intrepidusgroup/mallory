class Subject(object):
    """
    This is the implementation of the pub sub model used throughout Mallory
    to allow objects to easily communicate with one another while reducing
    coupling. 
    
    For any objects that wish to participate in the pub/sub model they must
    both inherit this class. 
    """
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        """
        When this is called the passed in observer is added to the list of
        objects that are interested in updates and activity. 
        
        When the object (which can have many attached observers) has something
        of interest, it fires the C{observer.Subject.notify} method. 
        
        @param observer: The observer that wants notification of updates
        @type object: any C{observer.Subject}
        """
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        """
        De-register a particular observer's interest in this objects activities

        @param observer: The observer that wants notification of updates
        @type object: any C{observer.Subject}        
        """
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, **kwargs):
        """
        When a C{observer.Subject} has something interest to tell its observers
        it calls this method, which will in turn call each observer's update
        method. 
        
        There is an implied interface here. If you want to receive 
        notifications you must implement an update(self, **kwags) method.
        
        kwargs is used to maintain ultimate flexibility at a cost of a little
        messiness in interpreting arguments in some places.

        @param kwargs: Keyworded arguments. Pretty much anything goes. 
        """
        for observer in self._observers:
            observer.update(self, **kwargs)