from gi.repository import GObject

class List(GObject.GObject):
    __gsignals__ = {
        "appended": (GObject.SIGNAL_RUN_FIRST, None, tuple()),
        "removed": (GObject.SIGNAL_RUN_FIRST, None, tuple()),
    }
    def __init__(self):
        super().__init__()

        self.__list = []
    
    def __len__(self):
        return len(self.__list)

    def __getitem__(self, index):
        if index > len(self.__list):
            raise IndexError()
        
        return self.__list[index]

    def append(self, item):
        self.__list.append(item)
        self.emit("appended")
    
    def remove(self, item):
        self.__list.remove(item)
        self.emit("removed")