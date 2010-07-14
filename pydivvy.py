from Tkinter import *
import commands

def placeWindow(x,y,w,h):
    cmd = "wmctrl -r :SELECT: -e 0,{x:d},{y:d},{w:d},{h:d}".format(x=x,y=y,w=w,h=h)
    o = commands.getoutput(cmd)
    print o

def getWorkArea():
   """ Return workarea geometry of current desktop
       (this means the area without panels)

       Use 2-tuple (x, y)
   """
   for line in commands.getoutput('wmctrl -d').split('\n'):
       if '*' in line: # '*' marks current desktop
           break
   geometry = line.split(None, 9)[8]
   return tuple(map(int, geometry.split('x')))
    
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



class App(Frame):
    def __init__(self, master=None, width=300, height=200, rows=6, cols=10):
        Frame.__init__(self, master)

        self.rows = rows
        self.cols = cols
        self.width = width
        self.height = height
        self.lastcol= 0
        self.lastrow = 0
        self.screenwidth = getWorkArea()[0] #self.master.winfo_screenwidth()
        self.screenheight = getWorkArea()[1]#self.master.winfo_screenheight()
        self.screen_width_ranges = splitCeil(range(self.screenwidth), cols)
        self.screen_height_ranges = splitCeil(range(self.screenheight), rows)
        self.window_width_ranges = splitCeil(range(width), cols)
        self.window_height_ranges = splitCeil(range(height), rows)

        self.gridColor = "DarkGrey"
        self.selectionColor = "red"

        if (master is not None):
            self.master.title("pydivvy")
            self.master.resizable(False,False)
            self.master.maxsize(self.width, self.height)
            self.master.minsize(self.width, self.height)

        self.pack()
        self.createWidgets()
        self.drawGrid();
        self.centerWindow()
       

    def drawGrid(self):
        for r in self.window_width_ranges:
            self.canvas.create_line(r[0], 0, r[0], self.height, fill=self.gridColor)

        for r in self.window_height_ranges:
            self.canvas.create_line(0, r[0], self.width, r[0], fill=self.gridColor)



    def centerWindow(self):
        ws = self.screenwidth
        hs = self.screenheight

        w, h = self.width, self.height
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def createWidgets(self):
        self.master.wm_attributes("-alpha", 0.3) #doesnt work.
        self.canvas = Canvas(self, width=self.width, height=self.height)
        
        self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Button-1>", self.setLastCell)
        self.canvas.bind("<B1-Motion>", self.drawRect)
        self.canvas.bind("<B1-ButtonRelease>", self.doneStroke)

    def getAreaDict(self, curr_x, curr_y, ranges_x, ranges_y):
        current_col = [i for (i, rng) in enumerate(self.window_width_ranges) if curr_x in rng][0]
        current_row = [i for (i, rng) in enumerate(self.window_height_ranges) if curr_y in rng][0]

        prev_col, prev_row = self.lastcol, self.lastrow
        
        ranges_w = ranges_x
        ranges_h = ranges_y
        
        disp_x = min(ranges_w[prev_col][0], \
                     ranges_w[prev_col][-1], \
                     ranges_w[current_col][0], \
                     ranges_w[current_col][-1])

        disp_y = min(ranges_h[prev_row][0], \
                     ranges_h[prev_row][-1], \
                     ranges_h[current_row][0], \
                     ranges_h[current_row][-1])

        disp_x2 = max(ranges_w[prev_col][0],\
                      ranges_w[prev_col][-1],\
                      ranges_w[current_col][0],\
                      ranges_w[current_col][-1])

        disp_y2 = max(ranges_h[prev_row][0],\
                      ranges_h[prev_row][-1],\
                      ranges_h[current_row][0],\
                      ranges_h[current_row][-1])

        return dict(min_x=disp_x, max_x=disp_x2, min_y=disp_y, max_y=disp_y2)        

    #------------ callbacks-------------------
    def setLastCell(self, event):
        lastx, lasty = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        col = [i for (i, rng) in enumerate(self.window_width_ranges) if lastx in rng][0]
        row = [i for (i, rng) in enumerate(self.window_height_ranges) if lasty in rng][0]
        
        self.lastcol, self.lastrow = col, row


    def drawRect(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(ALL)
        self.drawGrid()

        d = self.getAreaDict(x, y, self.window_width_ranges, self.window_height_ranges)
        x1, x2, y1, y2 = d["min_x"], d["max_x"], d["min_y"], d["max_y"]

        self.canvas.create_rectangle((x1, y1, x2, y2),\
                                     width=2,\
                                     outline=self.selectionColor)


    def doneStroke(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        d = self.getAreaDict(x, y, self.screen_width_ranges, self.screen_height_ranges)
        disp_x, disp_x2, disp_y, disp_y2 = d["min_x"], d["max_x"], d["min_y"], d["max_y"]
        
        width  = disp_x2 - disp_x
        height = disp_y2 - disp_y
        
        placeWindow(disp_x, disp_y, width, height)

     
root = Tk()
myapp = App(master=root, width=800, height=600, rows=6, cols=6)
myapp.mainloop()
