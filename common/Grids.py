import re
import sys
import time
import sched
import threading
import json
import os
from datetime import datetime,timedelta
from pprint import pprint
from functools import partial

import tkinter as tk
from tkinter import ttk, font, filedialog, messagebox

FONT = ("BIZ UDゴシック",20)
HOURS = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
MINUTES = ['00','10','20','30','40','50']

def ms(s):
    m = int(s/ 60)
    s = round(s - m*60, 1)
    if m > 0:
        return f"{m}分{s}秒"
    else:
        return f"{s}秒"
class GRIDS:
    LABEL = 1
    INPUT = 2
    BUTTONS = 3
    SELECT = 4
    PROGRESS_BAR = 5
    MESSAGE = 6
    TIME = 7
    FILE_OPEN = 8
    FILE_SAVE = 9
    INPUT_READONLY = 10
    OPTION_MENU = 11

class CustomGrid:
    tkElements = {}
    checks = {}
    start_times = {}
    current_values = {}
    def __init__(self, settings):
        self.tkElements = {}
        self.tkSelectLists = {}
        self.root = tk.Tk()
        self.root.title(settings["title"])
        self.root.geometry(f"{settings['width']}x{settings['height']}+0+0")
  
        r = 0
        pad = 4
        
        for gs in settings["grids"]:
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_columnconfigure(1, weight=4)
            if gs["type"] == GRIDS.LABEL:
                tkEle = tk.Label(self.root, text=gs["caption"],font=FONT,anchor=tk.CENTER)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W+tk.E,columnspan=2)
            if gs["type"] == GRIDS.INPUT:
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W)
                en_list = tk.Entry(self.root,  font=FONT, width=24)
                en_list.insert(0, gs["init"])
                en_list.grid(padx=pad, pady=pad, row=r,column=1,sticky=tk.W+tk.E)
                self.tkElements[gs["name"]] = en_list
                if "check" in gs:
                    self.checks[gs["name"]] = {
                        "name":gs["name"],
                        "label":gs["label"],
                        "check":gs["check"]
                    }
            if gs["type"] == GRIDS.INPUT_READONLY:
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W)
                en_list = tk.Entry(self.root,  font=FONT, width=24)
                en_list.insert(0, gs["init"])
                en_list.config(state="disabled")
                en_list.grid(padx=pad, pady=pad, row=r,column=1,sticky=tk.W+tk.E)
                self.tkElements[gs["name"]] = en_list
            if gs["type"] == GRIDS.BUTTONS:
                fr_buttons = ttk.Frame(self.root)
                fr_buttons.grid(padx=pad, pady=pad, row=r,column=0,columnspan=2)
                col = 0
                for bt in gs["buttons"]:
                    bt = tk.Button(fr_buttons, text=bt["caption"], command=partial(bt["callback"], self), font=FONT)
                    bt.grid(padx=pad, pady=pad, row=0, column=col)
                    col = col + 1
            if gs["type"] == GRIDS.TIME:
                hours, minutes = gs["init"].split(":")
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W)
                fr_times = ttk.Frame(self.root)
                fr_times.grid(padx=pad, pady=pad, row=r,column=1,sticky=tk.W)
                cb_hour = ttk.Combobox(fr_times, width=4, values=HOURS, state='readonly', font=FONT)
                cb_hour.set(hours)
                cb_hour.grid(padx=pad, pady=pad, row=0,column=0,sticky=tk.W)
                lb_sep = tk.Label(fr_times, text=':', height=2, width=1, font=FONT)
                lb_sep.grid(padx=pad, pady=pad, row=0,column=1,sticky=tk.W)
                cb_minute = ttk.Combobox(fr_times, width=4, values=MINUTES, state='readonly',font=FONT)
                cb_minute.set(minutes)
                cb_minute.grid(padx=pad, pady=pad, row=0,column=2,sticky=tk.W)
                self.tkElements[gs["name"]+"_HOUR"] = cb_hour
                self.tkElements[gs["name"]+"_MINUTE"] = cb_minute
            if gs["type"] == GRIDS.FILE_OPEN:
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W)
                fr = ttk.Frame(self.root)
                fr.grid(padx=pad, pady=pad, row=r,column=1,sticky=tk.W+tk.E)
                fileEnt = tk.Entry(fr, font=FONT, width=24)
                fileEnt.grid(padx=pad, pady=pad,row=0,column=0,sticky=tk.W+tk.E)
                bt = tk.Button(fr, text="開く", command=partial(self.open_file, gs["name"], gs["title"],gs["file_type"],gs["init"]), font=FONT)
                bt.grid(padx=pad, pady=pad,row=0,column=1,sticky=tk.E)
                self.tkElements[gs["name"]] = fileEnt
            if gs["type"] == GRIDS.FILE_SAVE:
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad, row=r, column=0,sticky=tk.W)
                fr = ttk.Frame(self.root)
                fr.grid(padx=pad, pady=pad, row=r,column=1,sticky=tk.W+tk.E)
                fileEnt = tk.Entry(fr, font=FONT, width=24)
                fileEnt.grid(padx=pad, pady=pad,row=0,column=0,sticky=tk.W+tk.E)
                bt = tk.Button(fr, text="保存", command=partial(self.save_file, gs["name"], gs["title"],gs["ext"],gs["file_type"],gs["init"]), font=FONT)
                bt.grid(padx=pad, pady=pad,row=0,column=1,sticky=tk.E)
                self.tkElements[gs["name"]] = fileEnt
            if gs["type"] == GRIDS.SELECT:
                tkEle = tk.Label(self.root, text=gs["label"],font=FONT,anchor=tk.W)
                tkEle.grid(padx=pad, pady=pad,row=r, column=0,sticky=tk.W)
                cb = ttk.Combobox(self.root, width=4, values=gs["list"], state='readonly', font=('BIZ UDゴシック', 20))
                cb.set(gs["init"])
                cb.bind("<<ComboboxSelected>>", partial(gs["onSelect"], self))

                cb.grid(padx=pad, pady=pad, row=r, column=1,sticky=tk.W+tk.E)
                self.tkElements[gs["name"]] = cb
                self.tkSelectLists[gs["name"]] = gs["list"]
            if gs["type"] == GRIDS.PROGRESS_BAR:
                en_list = tk.Entry(self.root, justify="center",  font=('BIZ UDゴシック', 20), width=24, state="readonly")
                en_list.insert(0, "")
                self.tkElements[gs["name"]+"_DISP"] = en_list
                en_list.grid(padx=pad, pady=pad,row=r, column=0,sticky=tk.W+tk.E,columnspan=2)
                r = r + 1
                pg = ttk.Progressbar(self.root, orient="horizontal", length=settings["width"]*0.8, mode="determinate")
                self.tkElements[gs["name"]] = pg
                pg.grid(padx=pad, pady=pad,row=r, column=0,sticky=tk.W+tk.E,columnspan=2)
            if gs["type"] == GRIDS.MESSAGE:
                tkM = tk.Text(self.root, state="disabled", font=("BIZ UDゴシック", 15),fg="#ff0000",height=gs["lines"])
                tkM.grid(padx=pad, pady=pad, row=r, column=0,columnspan=2,sticky=tk.W+tk.E)
                self.tkElements[gs["name"]] = tkM
            r=r+1
        self.root.mainloop()
    
    def destroy(self):
        self.root.destroy()
        
    def update(self):
        self.root.update()
        
    def confirm(self, title, message):
        return messagebox.askokcancel(title, message)
    
    def open_file(self, name, title, type, initDir):
    # ファイル選択ダイアログを開く
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=type,
            initialdir=initDir  # 初期ディレクトリを設定
        )
        if file_path:
            ent = self.tkElements[name]
            ent.delete(0, tk.END)
            ent.insert(0, file_path)
    def save_file(self, name, title, ext, type, initDir):
        # ファイル保存ダイアログを表示
        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,  # デフォルトの拡張子
            filetypes=type,
            title=title,
            initialdir=initDir
        )
        if file_path:  # ユーザーがファイルを選択した場合
            ent = self.tkElements[name]
            ent.delete(0, tk.END)
            ent.insert(0, file_path)
    def setMessage(self, name, text):
        tx = self.tkElements[name]
        tx.config(state="normal")
        tx.delete(1.0, tk.END)
        tx.insert(tk.END, text)
        tx.config(state="disabled")
        self.update_idletasks()
    def getValue(self, name):
        return self.tkElements[name].get()
    def getSelectedIndex(self, name):
        val = self.getValue(name)
        lists = self.tkSelectLists[name]
        idx = 0
        for list in lists:
            if val == list:
                return idx
            idx += 1
        return -1
    def setReadOnlyValue(self, name, value):
        tx = self.tkElements[name]
        tx.config(state="normal")
        tx.delete(0, tk.END)
        tx.insert(0, value)
        tx.config(state="disabled")
        self.update_idletasks()
    def getTime(self, name):
        return self.tkElements[name+"_HOUR"].get() + ":" + self.tkElements[name+"_MINUTE"].get()
    def getObject(self, name):
        return self.tkElements[name]
    def getProgressBar(self, name):
        return self.tkElements[name]
    def set_progress_value(self, name, value):
        self.tkElements[name]["value"] = value
    def set_progress_max_value(self, name, value):
        self.tkElements[name]["maximum"] = value
    def start_progress_bar(self, name, maxValue):
        self.start_times[name] = time.time()
        self.tkElements[name]["maximum"] = maxValue
        self.current_values[name] = 0
        self.update_idletasks()
    def set_progress(self, name, value):
        self.current_values[name] = value
        self.tkElements[name]["value"] = value
        remain = self.tkElements[name]["maximum"] - value
        ela = time.time() - self.start_times[name]
        if value > 0:
            ave = ela / value
            zan = round(remain * ave, 1)
            tx = self.tkElements[name+"_DISP"]
            msg = f"経過:{ms(ela)} {value}/{self.tkElements[name]["maximum"]} 残り:{ms(zan)}"
            tx.config(state="normal")
            tx.delete(0, tk.END)
            tx.insert(0, msg)
            tx.config(state="disabled")
            self.update_idletasks()
    def update_idletasks(self):
        self.root.update_idletasks()
    def check(self):
        print('CHECK')
        message = ""
        for ck in self.checks:
            print(ck)
            check = self.checks[ck]
            v = self.tkElements[check["name"]].get()
            print(f"input value={v}")
            print(check["check"])
            if "require" in check["check"]:
                if check["check"]["require"] == True:
                    if v == "":
                        message = message + f"「{check["label"]}」は必須です\n"
                        continue
            if "min_length" in check["check"]:
                ml = check["check"]["min_length"]
                if len(v) < ml:
                    message = message + f"「{check["label"]}」は{ml}文字以上です\n"
            if "max_length" in check["check"]:
                ml = check["check"]["max_length"]
                if len(v) > ml:
                    message = message + f"「{check["label"]}」は{ml}文字以内です\n"
            if "numeric" in check["check"]:
                if v.isdigit() == False:
                    message = message + f"「{check["label"]}」は数値で入力してください\n"
            if "pattern" in check["check"]:
                pat = check["check"]["pattern"]
                result = re.match(pat, v)
                if result == None:
                    message = message + f"「{check["label"]}」が無効です\n"
        return message



