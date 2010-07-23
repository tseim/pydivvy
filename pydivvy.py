from Tkinter import *
import commands
import os
import ConfigParser
import logging

PROGRAM_NAME = "pydivvy"

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
log.name = PROGRAM_NAME

def initconfig():
    rcfile = os.getenv("HOME") + "/.pydivvyrc"
    
    defaults = {
        'WindowWidth': 800,
        'WindowHeight' : 600,
        'Columns' : 8,
        'Rows' : 6,
        'GridColor' : 'DarkGrey',
        'SelectionColor' : 'red',
        'BackgroundColor' : '#303030'}
    config = ConfigParser.RawConfigParser(defaults)

    if not os.path.exists(rcfile):
        with open(rcfile, 'w') as f:
            config.write(f)

    config.read(rcfile)
    return config
        

def placeWindow(x,y,w,h):
    cmd = "wmctrl -r :SELECT: -e 0,{x:d},{y:d},{w:d},{h:d}".format(x=x,y=y,w=w,h=h)
    log.debug("Placing window: " + cmd)
    commands.getoutput(cmd)
    

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
    def __init__(self, master=None):
        Frame.__init__(self, master)
        
        
        self.initialize()

        self.lastcol= 0
        self.lastrow = 0
        self.screenwidth = getWorkArea()[0]
        self.screenheight = getWorkArea()[1]
        self.screen_width_ranges = splitCeil(range(self.screenwidth), self.cols)
        self.screen_height_ranges = splitCeil(range(self.screenheight), self.rows)
        self.window_width_ranges = splitCeil(range(self.width), self.cols)
        self.window_height_ranges = splitCeil(range(self.height), self.rows)

        
        if (master is not None):
            self.master.title(PROGRAM_NAME)
            self.master.bind("<Escape>", lambda e: self.master.quit())
            self.master.resizable(False,False)
            self.master.maxsize(self.width, self.height)
            self.master.minsize(self.width, self.height)

        self.pack()
        self.createWidgets()
        self.drawGrid();
        self.centerWindow()

    def initialize(self):
        config = initconfig()
        section = "DEFAULT"
        self.cols = config.getint(section, 'Columns')
        self.rows = config.getint(section, 'Rows')
        self.gridcolor = config.get(section, 'GridColor')
        self.selectioncolor = config.get(section, 'SelectionColor')
        self.width = config.getint(section, 'WindowWidth')
        self.height = config.getint(section, 'WindowHeight')
        self.backgroundcolor = config.get(section, 'BackgroundColor')
       

    def drawGrid(self):
        for r in self.window_width_ranges:
            self.canvas.create_line(r[0], 0, r[0], self.height, fill=self.gridcolor)

        for r in self.window_height_ranges:
            self.canvas.create_line(0, r[0], self.width, r[0], fill=self.gridcolor)



    def centerWindow(self):
        ws = self.screenwidth
        hs = self.screenheight

        w, h = self.width, self.height
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def createWidgets(self):
        self.master.wm_attributes("-alpha", 0.3) #doesnt work.
        self.canvas = Canvas(self, width=self.width, height=self.height, bg=self.backgroundcolor)
        
        self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Button-1>", self.setLastCell)
        self.canvas.bind("<B1-Motion>", self.drawRect)
        self.canvas.bind("<B1-ButtonRelease>", self.doneStroke)
        self.canvas.bind("<Escape>", self.quit)
        

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
    def quit(self, event):
        Frame.quit(self)

    def setLastCell(self, event):
        lastx, lasty = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        col = [i for (i, rng) in enumerate(self.window_width_ranges) if lastx in rng][0]
        row = [i for (i, rng) in enumerate(self.window_height_ranges) if lasty in rng][0]
        
        self.lastcol, self.lastrow = col, row


    def drawRect(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete(ALL)
        self.drawGrid()
        
        x = 0 if x < 0 else min(x, self.width - 1) 
        y = 0 if y < 0 else min(y, self.height - 1)
        
        d = self.getAreaDict(x, y, self.window_width_ranges, self.window_height_ranges)
        x1, x2, y1, y2 = d["min_x"], d["max_x"], d["min_y"], d["max_y"]

        self.canvas.create_rectangle((x1, y1, x2, y2),\
                                     width=2,\
                                     outline=self.selectioncolor)


    def doneStroke(self, event):
        x,y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        d = self.getAreaDict(x, y, self.screen_width_ranges, self.screen_height_ranges)
        disp_x, disp_x2, disp_y, disp_y2 = d["min_x"], d["max_x"], d["min_y"], d["max_y"]
        
        width  = disp_x2 - disp_x
        height = disp_y2 - disp_y
        
        placeWindow(disp_x, disp_y, width, height)

     
root = Tk()
myapp = App(master=root)
myapp.mainloop()
