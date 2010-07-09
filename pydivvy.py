from Tkinter import *
import re
import commands
import subprocess


def getWorkArea():
    """ Return workarea geometry of current desktop
        (this means the area without panels)

        Use 2-tuple (x, y)
    """
    for line in commands.getoutput("wmctrl -d").split("\n"):
        if '*' in line: # '*' marks current desktop
            break
    geometry = line.split(None, 9)[8]
    return tuple(map(int, geometry.split('x')))

def kill_wmctrl():
    cmd = "killall wmctrl"
    subprocess.Popen(cmd,shell=True)
    #o = commands.getoutput(cmd)
    #print o

def placeWindow(x,y,w,h):
    cmd = "wmctrl -r :SELECT: -e 0,{x:d},{y:d},{w:d},{h:d}".format(x=x,y=y,w=w,h=h)
    o = commands.getoutput(cmd)
    print o

    
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


def getBlockBounds(val, end, num_blocks):
    seq=range(end)
    n,b,newseq=len(seq),0,[]
    for k in range(num_blocks):
        q,r=divmod(n-k,num_blocks)
        a,b=b,b+q+(r!=0)
        if val in seq[a:b]:
            return seq[a], seq[b-1]

def parseGeometry(geometry):
    m = re.match("(\d+)x(\d+)([-+]\d+)([-+]\d+)", geometry)
    if not m:
        raise ValueError("failed to parse geometry string")
    return map(int, m.groups())


class App(Frame):
    def __init__(self, master=None, width=300, height=200, rows=6, cols=10):
        Frame.__init__(self, master)

        self.lastcoords = []
        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height

        self.x1 = self.y1 = self.x2 = self.y2 = 0
        
        if (master is not None):
            self.master.title("Selector")
            self.master.resizable(False,False)
            self.master.maxsize(self.width, self.height)
            self.master.minsize(self.width, self.height)

        self.pack()
        self.createWidgets()
        self.drawGrid();
        self.centerWindow()
        #self.master.overrideredirect(False)

    def drawGrid(self):
        ranges = splitCeil(range(self.width), self.cols)
        for r in ranges:
            self.canvas.create_line(r[0],0,r[0],self.height, fill="red")

        ranges = splitCeil(range(self.height),self.rows)
        for r in ranges:
            self.canvas.create_line(0,r[0],self.width,r[0], fill="red")



    def centerWindow(self):
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()

        w, h = self.width, self.height
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def createWidgets(self):
        self.canvas = Canvas(self, width=self.width, height=self.height)
        
        self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Button-1>", self.updateXY)
        self.canvas.bind("<B1-Motion>", self.drawRect)
        self.canvas.bind("<B1-ButtonRelease>", self.doneStroke)
        self.canvas.bind("<Button-3>", self.rightClick)

    

    def getCoords(self, x, y):
        w,h,xoff,yoff = parseGeometry(self.master.geometry());
        rx = getBlockBounds(x, w, self.cols)
        ry = getBlockBounds(y, h, self.rows)
        return rx,ry


    #------------ callbacks-------------------
    def updateXY(self, event):
        lastx, lasty = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        crds = self.getCoords(lastx,lasty)
        self.lastcoords = crds

    def drawRect(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(ALL)
        self.drawGrid()
        newcoords= self.getCoords(x,y);
        lastcoords= self.lastcoords
        x1 = min(newcoords[0][0], newcoords[0][1], lastcoords[0][0], lastcoords[0][1])
        y1 = min(newcoords[1][1], newcoords[1][0], lastcoords[1][1], lastcoords[1][0])
        x2 = max(newcoords[0][0], newcoords[0][1], lastcoords[0][0], lastcoords[0][1])
        y2 = max(newcoords[1][1], newcoords[1][0], lastcoords[1][1], lastcoords[1][0])

        self.x1 = min(x1,x2)
        self.y1 = min(y1,y2)
        self.x2 = max(x2,x1)
        self.y2 = max(y2,y1)
        
        self.canvas.create_rectangle((self.x1, self.y1, self.x2, self.y2), width=2)

    def doneStroke(self, event):
        #disp_w,disp_h,xoff,yoff = parseGeometry(self.master.geometry())

        width, height = self.x2-self.x1+1, self.y2-self.y1+1
        disp_w,disp_h = getWorkArea()
        factor_w = float(disp_w)/self.width
        factor_h = float(disp_h)/self.height
        
        print factor_h, factor_w
        print "x1={0}, y1={1}, x2={2}, y2={3}, width={4}, height={5}".format(self.x1,self.y1,self.x2,self.y2,width,height)
        placeWindow(int(self.x1*factor_w), int(self.y1*factor_h), int(width*factor_w), int(height*factor_h))

    def rightClick(self,event):
        kill_wmctrl()



root = Tk()
#root.columnconfigure(0, weight=1)
#root.rowconfigure(0, weight=1)
myapp = App(master=root, width=800, height=600)
myapp.mainloop()
