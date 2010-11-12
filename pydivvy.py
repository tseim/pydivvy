from Tkinter import *
import commands
import os
import ConfigParser
import logging

PROGRAM_NAME = "pydivvy"

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
log.name = PROGRAM_NAME

def init_config():
    rcfile = os.getenv("HOME") + "/.pydivvyrc"
    
    defaults = {
        'WindowWidth': 800,
        'WindowHeight' : 600,
        'Columns' : 8,
        'Rows' : 6,
        'GridColor' : 'DarkGrey',
        'SelectionColor' : 'red',
        'BackgroundColor' : '#303030',
        'DecorationHeight': 15}
    config = ConfigParser.RawConfigParser(defaults)

    if not os.path.exists(rcfile):
        with open(rcfile, 'w') as f:
            config.write(f)

    config.read(rcfile)
    return config
        

def place_window(x, y, w, h, skip):
    """ Runs wmctrl using the given dimensions as parameter.
        The user has to select a window to apply the changes.
    """
    cmd = "wmctrl -r :SELECT: -e 0,{x:d},{y:d},{w:d},{h:d}".format(x=x,y=y,w=w,h=h-skip)
    log.debug("Placing window: " + cmd)
    commands.getoutput(cmd)
    

def get_work_area():
   """ Return workarea geometry of current desktop
       (this means the area without panels)

       Use 2-tuple (x, y)
   """
   for line in commands.getoutput('wmctrl -d').split('\n'):
       if '*' in line: # '*' marks current desktop
           geometry = line.split(None, 9)
           min_x, min_y = geometry[7].split(',')
           max_x, max_y = geometry[8].split('x')
   
   return int(min_x), int(min_y), int(max_x), int(max_y) 
    
def split_ceil(seq, m):
    """Distribute the seq elements in lists in m groups
       according to quasi equitative distribution (decreasing order):
         split_ceil(range(13), 4) --> seq = range(13), m=4
         result : [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    """
    n,b,newseq = len(seq),0,[]
    for k in range(m):
        q, r = divmod(n - k, m)
        a, b = b, b + q + (r != 0)
        newseq.append(seq[a:b])
    return newseq



class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.initialize()

        self.lastcol = self.lastrow = 0
        self.min_x, self.min_y, self.screenwidth, self.screenheight = get_work_area()
        self.screen_width_ranges = split_ceil(range(self.min_x, self.screenwidth), self.cols)
        self.screen_height_ranges = split_ceil(range(self.min_y, self.screenheight), self.rows)
        self.window_width_ranges = split_ceil(range(self.width), self.cols)
        self.window_height_ranges = split_ceil(range(self.height), self.rows)

        self.master.title(PROGRAM_NAME)
        self.master.bind("<Escape>", lambda e: self.master.quit())
        self.master.resizable(False,False)
        self.master.maxsize(self.width, self.height)
        self.master.minsize(self.width, self.height)

        self.pack()
        self.create_widgets()
        self.draw_grid();
        self.center_window()

    def initialize(self):
        config = init_config()
        section = "DEFAULT"
        self.cols = config.getint(section, 'Columns')
        self.rows = config.getint(section, 'Rows')
        self.gridcolor = config.get(section, 'GridColor')
        self.selectioncolor = config.get(section, 'SelectionColor')
        self.width = config.getint(section, 'WindowWidth')
        self.height = config.getint(section, 'WindowHeight')
        self.backgroundcolor = config.get(section, 'BackgroundColor')
        self.decoration_height = config.getint(section, 'DecorationHeight')


    def draw_grid(self):
        for r in self.window_width_ranges:
            self.canvas.create_line(r[0], 0, r[0], self.height, fill=self.gridcolor)

        for r in self.window_height_ranges:
            self.canvas.create_line(0, r[0], self.width, r[0], fill=self.gridcolor)


    def center_window(self):
        ws = self.screenwidth
        hs = self.screenheight

        w, h = self.width, self.height
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def create_widgets(self):
        self.master.wm_attributes("-alpha", 0.3) #doesnt work.
        self.canvas = Canvas(self, width=self.width, height=self.height, bg=self.backgroundcolor)
        
        self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Button-1>", self.set_last_cell)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<B1-ButtonRelease>", self.done_stroke)
        self.canvas.bind("<Escape>", self.quit)


    def get_area_coordinates(self, curr_x, curr_y, ranges_w, ranges_h):
        current_col = [i for (i, rng) in enumerate(self.window_width_ranges) if curr_x in rng][0]
        current_row = [i for (i, rng) in enumerate(self.window_height_ranges) if curr_y in rng][0]

        prev_col, prev_row = self.lastcol, self.lastrow
        
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

        return disp_x, disp_x2, disp_y, disp_y2     


    def quit(self, event):
        Frame.quit(self)


    def set_last_cell(self, event):
        lastx, lasty = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        col = [i for (i, rng) in enumerate(self.window_width_ranges) if lastx in rng][0]
        row = [i for (i, rng) in enumerate(self.window_height_ranges) if lasty in rng][0]
        
        self.lastcol, self.lastrow = col, row


    def limit_cursor_position(self, event_x, event_y):
        x, y = self.canvas.canvasx(event_x), self.canvas.canvasy(event_y)
        x = 0 if x < 0 else min(x, self.width - 1) 
        y = 0 if y < 0 else min(y, self.height - 1)
        return x, y
        
        
    def draw_rectangle(self, event):
        x, y = self.limit_cursor_position(event.x, event.y)

        self.canvas.delete(ALL)
        self.draw_grid()
        
        x1, x2, y1, y2 = self.get_area_coordinates(x, y, self.window_width_ranges, self.window_height_ranges)

        self.canvas.create_rectangle((x1, y1, x2, y2),\
                                     width=2,\
                                     outline=self.selectioncolor, \
                                     fill='')


    def done_stroke(self, event):
        x, y = self.limit_cursor_position(event.x, event.y)

        x1, x2, y1, y2 = self.get_area_coordinates(x, y, self.screen_width_ranges, self.screen_height_ranges)
        
        width  = x2 - x1
        height = y2 - y1
        
        place_window(x1, y1, width, height, self.decoration_height)

     
root = Tk()
pydivvy = App(master=root)
pydivvy.mainloop()
