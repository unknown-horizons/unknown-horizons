class Move:
    def __init__(self, a, b):
        self.stuff = [a,b]
    def __call__(self, units, **trash):
        print "units:",units,"self.stuff:",self.stuff,"trash:",trash