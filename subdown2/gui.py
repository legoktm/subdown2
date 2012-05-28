#!/usr/bin/python
from Tkinter import *
import __init__ as subdown2


class Application(Frame):

    def __init__(self, master=None):
      Frame.__init__(self, master)
      self.grid()
      self.createWidgets()
      
    def go(self):
      subreddits = self.sr_input.get()
      pages = int(self.pg_input.get())
      for subreddit in subreddits.split(','):
        app = subdown2.Client(subreddit,pages)
        app.run()

    def createWidgets(self):
	
      #self.title = Label(self, text='subdown2')
      #self.title.grid(row=0, column=0, columnspan=5)

      self.srlabel = Label(self, text='Subreddit')
      self.srlabel.grid(row=0,column=0)
      
      self.subreddits = StringVar()
      self.sr_input = Entry(self, textvariable=self.subreddits, width=20)
      self.sr_input.grid(row=1, column=0)
      
      self.numlabel = Label(self, text='Pages?')
      self.numlabel.grid(row=0,column=2)
      
      self.pages = StringVar()
      self.pg_input = Entry(self, textvariable=self.pages, width=3)
      self.pg_input.grid(row=1, column=2)
      
      self.runB = Button(self, text='Download!', command=self.go)
      self.runB.grid(row=6,column=0)
      
      self.Slider = Scale(self, from_=0, to_=100, resolution=.1, orient=HORIZONTAL)
      self.Slider.grid(row=7, column=0)



def main():
  App = Application()
  App.master.title("subdown2")
  App.mainloop()
  
if __name__ == "__main__":
  main()