from Tkinter import *
import re
    
def splitCeil(seq, m):
    """Distribute the seq elements in lists in m groups
       according to quasi equitative distribution (decreasing order):
         splitCeil(range(13), 4) --> seq = range(13), m=4
         result : [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    """
    n,b,newseq=len(seq),0,[]
    for k in range(m):
        q,r=divmod(n-k,m)
        a, b = b, b + q + (r!=0)
        newseq.append(seq[a:b])
    return newseq

def getMinMax(val, seq, g):
    mini = maxi = 0
    for seq in splitCeil(range(seq),g):
        if val in seq:
            return seq[0], seq[-1]

def parseGeometry(geometry):
    m = re.match("(\d+)x(\d+)([-+]\d+)([-+]\d+)", geometry)
    if not m:
        raise ValueError("failed to parse geometry string")
    return map(int, m.groups())



class App(Frame):
    def __init__(self, master=None, width=300, height=200, rows=6, cols=10):
        Frame.__init__(self, master)

        self.lastx = self.lasty = 0
        self.rows = rows
        self.cols = cols
        
        if (master is not None):
            self.master.title("Selector")
            self.master.resizable(False,False)
            self.master.maxsize(width, height)
            self.master.minsize(width, height)

        self.pack()
        self.createWidgets()
        self.center_window(width, height)
        self.master.overrideredirect(False)

    def center_window(self, w, h):
        # get screen width and height
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        # calculate position x, y
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def createWidgets(self):
        self.canvas = Canvas(self)
        self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Button-1>", self.updateXY)
        self.canvas.bind("<B1-Motion>", self.drawRect)
        self.canvas.bind("<B1-ButtonRelease>", self.doneStroke)
        self.canvas.bind("<Button-3>", quit)

    

    def getCoords(self, x, y):
        w,h,xoff,yoff = parseGeometry(self.master.geometry());
        rx = getMinMax(x, w, self.cols)
        ry = getMinMax(y, h, self.rows)
        return rx,ry


#------------ callbacks-------------------
    def updateXY(self, event):
        self.lastx, self.lasty = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        crds = self.getCoords(event.x,event.y)
        self.lastx = crds[0][0]
        self.lasty = crds[1][0]

    def drawRect(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(ALL)
        #print x,y
        crds= self.getCoords(x,y);
        x,y = crds[0][1], crds[1][1] 
        self.canvas.create_rectangle((self.lastx, self.lasty, x, y))#, tags='currentline')

    def doneStroke(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(ALL)
        crds= self.getCoords(x,y);
        x,y = crds[0][1], crds[1][1]
        self.canvas.create_rectangle((self.lastx, self.lasty, x, y))#, tags='currentline')
        self.lastx, self.lasty = x, y



root = Tk()

myapp = App(master=root)

def quit():
    root.quit()

myapp.mainloop()
#root.destroy()
