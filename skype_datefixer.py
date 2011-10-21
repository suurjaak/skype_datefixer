#!/usr/bin/env python
"""
Script for fixing future dates in Skype chat history. On running, lets the user
choose a Skype history file and shifts the timestamp of future messages to
the past by a specified number of days.

Background: message dates in Skype chat are given timestamps according to
computer date/time on message receival, and they are sorted in the chat history
by timestamp. For example, if the computer's date/time was one month in the
future when the messages were received, then after fixing the computer
date/time, new messages in Skype chat history will be added BEFORE the
incorrectly timestamped messages, making it very hard to use Skype chat until
the original future date is reached.

@author    Erki Suurjaak <erki@lap.ee>
@created   19.10.2011
@modified  20.10.2011
"""

import datetime
import sqlite3
import time
import Tkinter
import tkFileDialog
import tkMessageBox
import tkSimpleDialog


class SkypeDateFixer(Tkinter.Frame):
    """
    Displays a Tkinter visual application where user can choose a Skype history
    file and change message timestamps.
    """
    def __init__(self):
        self.master = Tkinter.Tk()
        Tkinter.Frame.__init__(self, master=self.master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.master.title("Skype Datefixer")

        textscrollbar = Tkinter.Scrollbar(self, orient=Tkinter.VERTICAL)
        textscrollbar.grid(row=0, column=3, sticky=Tkinter.N+Tkinter.S)
        self.text = Tkinter.Text(master=self, cnf={"height": 15, "font": ("Times", 10), "width": 100}, wrap=Tkinter.WORD, yscrollcommand=textscrollbar.set)
        textscrollbar.config(command=self.text.yview)
        self.text.grid(row=0, column=0, columnspan=3, sticky=Tkinter.N+Tkinter.S+Tkinter.E+Tkinter.W)
        self.log("Will let you re-date Skype messages that have future timestamps. Shut down Skype and choose your Skype chat history file (for Windows, tends to be\n'Documents and Settings\%windows username%\Application Data\Skype\%skype username%\main.db').")

        self.button_open = Tkinter.Button(master=self)
        self.button_open["text"] = "Open Skype chat database"
        self.button_open["command"] = self.open_file
        self.button_open.grid(row=1, column=0, sticky=Tkinter.W)

        self.button_update = Tkinter.Button(master=self)
        self.button_update["text"] = "Update database"
        self.button_update["command"] = self.update
        self.button_update["state"] = Tkinter.DISABLED
        self.button_update.grid(row=1, column=0, padx=100)

        self.button_quit = Tkinter.Button(master=self)
        self.button_quit["text"] = "Exit"
        self.button_quit["command"] = self.exit
        self.button_quit.grid(row=1, column=0, columnspan=4, sticky=Tkinter.E)

        self.pack()

        self.db = None
        self.cursor = None
        self.filename = None
        self.max_timestamp = None
        self.max_datetime = None
        self.now_timestamp = None
        self.now_datetime = None
        self.count_messages = None


    def log(self, message, *args):
        """Logs the message to the text box."""
        if args:
            message = message % args
        self.text.insert(Tkinter.END, message + "\n")
        self.text.yview(Tkinter.END) # Scroll to end


    def open_file(self):
        """Shows an "open file" dialog and opens the selected file as an SQLite database."""
        self.filename = tkFileDialog.askopenfilename(filetypes=[("SQLite databases", "*.db"), ("All files", "*.*")])
        if self.filename:
            self.now_timestamp = int(time.time())
            self.text.insert(Tkinter.END, "\nOpening file '%s'." % self.filename)
            try:
                if self.db:
                    self.db.close()
                self.db = sqlite3.connect(self.filename)
                self.cursor = self.db.cursor()
                res = self.cursor.execute("SELECT MAX(Timestamp) FROM Messages")
                self.max_timestamp = res.fetchall()[0][0] # UNIX timestamp
                res = self.cursor.execute("SELECT COUNT(*) FROM Messages WHERE Timestamp > ?", [self.now_timestamp])
                self.count_messages = res.fetchall()[0][0]
                self.max_datetime = datetime.datetime.fromtimestamp(self.max_timestamp)
                self.now_datetime = datetime.datetime.fromtimestamp(self.now_timestamp)
                self.log("\nLatest message timestamp in database is '%s', current datetime is '%s'.\nMaximum difference is %s days, %s messages are newer than now.", self.max_datetime.strftime('%Y-%m-%d %H:%M:%S'), self.now_datetime.strftime('%Y-%m-%d %H:%M:%S'), (self.max_datetime - self.now_datetime).days, self.count_messages)
                if self.max_timestamp < self.now_timestamp:
                    self.log("\nNothing needs doing in this database.")
                    self.button_update["state"] = Tkinter.DISABLED
                    self.db.close()
                    self.db = None
                else:
                    self.log("Click '%s' to specify the number of days to shift.", self.button_update["text"])
                    self.button_update["state"] = Tkinter.NORMAL
            except Exception, e:
                self.log("\nEither Skype is still running or '%s' is not a valid Skype history file (error '%s').", self.filename, e)


    def update(self):
        """Asks the user how many days to shift messages, and proceeds."""
        delta = self.max_datetime - self.now_datetime
        days_to_shift = tkSimpleDialog.askinteger("Days to shift", "Enter the number of days to shift messages, newer than the current time, into the past\n(delta between now and latest timestamp is %s days):" % delta.days)
        if days_to_shift:
            do_proceed = tkMessageBox.askokcancel("Proceed?", "Shift %s messages %s days into the past?" % (self.count_messages, days_to_shift))
            if do_proceed:
                self.log("\nUpdating..")
                self.cursor.execute("UPDATE Messages SET Timestamp = Timestamp - 60*60*24*?", [days_to_shift])
                self.db.commit()
                self.db.close()
                self.db = None
                self.log("Shifted %s messages %s days into the past. All complete.", self.count_messages, days_to_shift)
                self.button_update["state"] = Tkinter.DISABLED
        else:
            self.log("\n'%s' entered, not proceeding.", days_to_shift)


    def exit(self):
        if self.db:
            self.db.close()
        self.quit()


if "__main__" == __name__:
    application = SkypeDateFixer()
    application.mainloop()
