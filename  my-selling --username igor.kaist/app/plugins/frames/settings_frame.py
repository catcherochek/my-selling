#-*-coding:utf-8-*-
# окно  настроек программы
"""
    Copyright (C) 2010 Kozlov Igor <igor.kaist@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
from Tkinter import *
from ttk import *
import tkMessageBox as box
from  MultiListbox import MultiListbox
import md5py
from ScrolledText import ScrolledText
import zipfile
import os
import subprocess
import sys
import urllib
import json

from date_time import date_now,time_now,norm_date,int2date
import time

name='Настройки'
frame=2
#icon='clear'

class Plugin:
	def __init__(self,app):
		self.app=app
		
	def run(self):
		self.reload=False
		self.win=Toplevel(self.app.app.win)
		self.win.protocol("WM_DELETE_WINDOW", self.exit)
		self.win.title(name)
		x,y=700,300
		pos=self.win.wm_maxsize()[0]/2-x/2,self.win.wm_maxsize()[1]/2-y/2
		self.win.geometry('%sx%s+%s+%s'%(x,y,pos[0],pos[1]-25))	
		self.win.maxsize(width=x,height=y)
		self.win.minsize(width=x,height=y)
		if sys.platform=='win32':self.win.iconbitmap('app/images/icon.ico')
			
		self.nb=Notebook(self.win)
		self.nb.pack(fill=BOTH,expand=1,padx=5,pady=5)
		self.deps=Deps(self)
		self.pers=Personal(self)
		self.sync=Sync(self)
		self.upd=Updates(self)
		self.nb.add(self.deps.win, text='Отделы', padding=3,image=self.app.app.img['deps'],compound='left')
		self.nb.add(self.pers.win, text='Персонал', padding=3,image=self.app.app.img['people_mini'],compound='left')
		self.nb.add(self.sync.win, text='Синхронизация', padding=3,image=self.app.app.img['sync'],compound='left')
		self.nb.add(self.upd.win, text='Обновления', padding=3,image=self.app.app.img['updates'],compound='left')

	def exit(self,event=None):
		self.win.destroy()
		# если были сделаны изменения, просим перезапустить программу
		if self.reload:
			s=box.askokcancel(title='Настройки',message='После изменения настроек,\nтребуется перезапуск программы.\nПерезапустить?')
			if s:
				self.app.app.root.destroy()
				try:subprocess.Popen(sys.argv[0])
				except WindowsError,x:
					subprocess.Popen('pythonw '+sys.argv[0])
			
class Deps():
	def __init__(self,app):
		""" управление отделами """
		self.app=app
		self.win=Frame(self.app.win)
		self.lst=Listbox(self.win,width=25,height=10,font=('normal',12))
		self.lst.bind('<ButtonRelease-1>',self.lst_command)
		self.lst.grid(row=0,column=0,rowspan=20,padx=10,pady=10)
		self.edit_ent=Entry(self.win,width=23,font=('normal',14),cursor='xterm')
		self.edit_ent.grid(row=0,column=1,columnspan=2,pady=10,sticky=N)
		
		
		self.rb_var=IntVar()
		self.rb=Radiobutton(self.win,text='Не следить за остатками товара',value=0,variable=self.rb_var)
		self.rb.grid(row=1,column=1,sticky=W,padx=10,pady=10,columnspan=2)
		self.rb2=Radiobutton(self.win,text='Предупредить об отсутствии товара',value=1,variable=self.rb_var)
		self.rb2.grid(row=2,column=1,sticky=W,padx=10,pady=10,columnspan=2)
		self.rb3=Radiobutton(self.win,text='Запретить продажу при отсутствии товара',value=2,variable=self.rb_var)
		self.rb3.grid(row=3,column=1,sticky=W,padx=10,pady=10,columnspan=2)			
		
		
		self.del_but=Button(self.win,text='Не использовать',image=self.app.app.app.img['delete'],compound='left',command=self.del_dep)
		self.del_but.grid(row=4,column=1)
		self.save_but=Button(self.win,text='Сохранить',image=self.app.app.app.img['save'],compound='left',command=self.save)
		self.save_but.grid(row=4,column=2)	
		self.sel=None
		self.update_list()

	def update_list(self):
		""" список отделов """
		self.lst.delete(0,END)
		self.c_list=[]
		self.app.app.app.db.execute('select * from dep')
		for x in self.app.app.app.db.fetchall():
			self.lst.insert(END,str(x[0])+' '+x[1])
			self.c_list.append(x)
			
	def lst_command(self,event=None):
		""" при щелчке на отдел """
		if not self.lst.curselection():return
		self.sel=int(self.lst.curselection()[0])
		self.edit_ent.delete(0,END)
		self.edit_ent.insert(0,self.c_list[self.sel][1])
		self.rb_var.set(self.c_list[self.sel][2])
		
	def save(self):
		""" сохраняем изменения """
		if self.sel==None:return
		txt=self.edit_ent.get()
		v=self.rb_var.get()
		self.app.app.app.db.execute('update dep set name=?, warning=? where id=?',(txt,v,self.sel+1))
		self.app.app.app.con.commit()
		self.app.reload=True
		self.update_list()
		self.lst.selection_set(self.sel)


		
	def del_dep(self):
		""" при удалении отдела, тупо удаляем его название """
		if self.sel==None:return
		self.app.app.app.db.execute('update dep set name=? where id=?',('',self.sel+1))
		self.app.app.app.con.commit()
		self.app.reload=True
		self.update_list()
		self.lst.selection_set(self.sel)
		self.edit_ent.delete(0,END)


		
class Personal():
	def __init__(self,app):
		""" управление пользователями """
		self.app=app
		self.user_list=[]
		self.win=Frame(self.app.win)
		self.selected=None
		self.scr1=Scrollbar(self.win,orient=VERTICAL)
		self.scr1.grid(row=0,column=2,sticky=N+S,pady=10)
		self.lst=Listbox(self.win,width=30,height=10,
			font=("Arial", 10, "bold"),
			yscrollcommand=self.scr1.set)
		self.lst.grid(row=0,column=0,pady=10,columnspan=2)
		self.scr1['command']=self.lst.yview
		self.lst.bind('<ButtonRelease-1>',self.lst_command)
		
		
		self.add_ent=Entry(self.win,width=15,cursor='xterm')
		self.add_ent.grid(row=1,column=0)
		self.add_but=Button(self.win,text='Добавить',image=self.app.app.app.img['people_mini'],compound='left',width=8,command=self.add_user)
		self.add_but.grid(row=1,column=1)
		self.del_but=Button(self.win,text='Удалить',image=self.app.app.app.img['delete'],compound='left',command=self.del_user)
		self.del_but.grid(row=2,column=0,columnspan=2)
		
		self.frame=LabelFrame(self.win,text='Настройки пользователя',width=450)
		self.frame.grid(row=0,column=2,rowspan=5,sticky=N+E+S+W,padx=7)

		Label(self.frame,text='Пароль').grid(row=0,column=0,padx=5)
		
		self.pass_ent=Entry(self.frame,show='*',cursor='xterm')
		self.pass_ent.grid(row=0,column=1)
		self.pass_ent['state']='disable'
		self.pass_state=False
		self.pass_ch=Checkbutton(self.frame,text='Требовать пароль',command=self.ch_handler)
		self.pass_ch.grid(row=0,column=2,padx=5,pady=5)
		self.pass_ch.invoke()
		self.pass_ch.invoke()

		
		self.caps=LabelFrame(self.frame,text='Допустить к...')
		self.caps.grid(row=1,column=0,columnspan=3,padx=5)
		Label(self.caps,text='Нет доступа к...').grid(row=0,column=0)
		Label(self.caps,text='Есть доступ к...').grid(row=0,column=3)		
		self.scr2=Scrollbar(self.caps,orient=VERTICAL)
		self.scr2.grid(row=1,column=1,sticky=N+S,rowspan=5)
		self.lst2=Listbox(self.caps,width=20,height=7,
			font=("Arial", 10, "bold"),
			yscrollcommand=self.scr2.set)
		self.lst2.grid(row=1,column=0,rowspan=5)
		self.scr2['command']=self.lst2.yview
		#self.lst.bind('<ButtonRelease-1>',self.lst_command)

		self.scr3=Scrollbar(self.caps,orient=VERTICAL)
		self.scr3.grid(row=1,column=4,sticky=N+S,rowspan=5)
		self.lst3=Listbox(self.caps,width=20,height=7,
			font=("Arial", 10, "bold"),
			yscrollcommand=self.scr3.set)
		self.lst3.grid(row=1,column=3,rowspan=5)
		self.scr3['command']=self.lst3.yview
		
		self.right_but=Button(self.caps,text='>>',command=self.add_caps)
		self.right_but.grid(row=2,column=2)
		self.left_but=Button(self.caps,text='<<',command=self.del_caps)
		self.left_but.grid(row=3,column=2)
		
		self.save_user=Button(self.frame,text='Сохранить',image=self.app.app.app.img['save'],compound='left',command=self.save_changes)
		self.save_user.grid(row=3,column=2,sticky=E,padx=5,pady=2)


		
		self.update_list()

	def ch_handler(self):
		""" при смене чекбаттона "требовать пароль" """
		if self.pass_state:
			self.pass_state=False
			self.pass_ent['state']='disable'
		else:
			self.pass_state=True
			self.pass_ent['state']='normal'

	def update_list(self):
		""" обновляем список пользователей """
		self.user_list=[]
		self.app.app.app.db.execute('select name from users')
		self.lst.delete(0,END)
		for x in self.app.app.app.db.fetchall():
			self.lst.insert(END,x[0])
			self.user_list.append(x[0])
		self.selected=None
		
	def lst_command(self,event=None):
		""" при щелчке на допользователя, обновляем """
		if not self.lst.curselection():return
		self.selected=self.user_list[int(self.lst.curselection()[0])]
		self.update_frame()
		
	def add_user(self):
		""" добавление пользователя """
		usr=self.add_ent.get()
		if not usr:
			box.showerror(title='Ошибка',message='Вы должны ввести имя пользователя!')
			self.app.win.deiconify()
			return
		self.app.app.app.db.execute('insert into users values (?,?,?)',(usr,'','[]'))
		self.app.app.app.con.commit()
		self.update_list()
		self.add_ent.delete(0,END)
		self.app.reload=True
		
	def del_user(self): 
		""" удаляем пользователя """
		if not self.selected:return
		if self.selected==u'Администратор':
			box.showerror(title='Ошибка',message='Нельзя удалять Администратора!')
			self.app.win.deiconify()
			return			
		s=box.askyesno(title='Удаление',message='Вы уверены, что хотите удалить пользователя: %s'%(self.selected.encode('utf-8')))
		self.app.win.deiconify()
		if not s:return
		self.app.app.app.db.execute('delete from users where name=?',(self.selected,))
		self.app.app.app.con.commit()
		self.update_list()
		self.app.reload=True
		
	def update_frame(self):
		""" обновляем фрейм с настройкми пользователя """
		self.app.app.app.db.execute('select passw,caps from users where name=?',(self.selected,))
		self.passw,self.caps=self.app.app.app.db.fetchall()[0]
		self.caps=eval(self.caps)
		self.av_caps=[]
		if self.passw:
			if not self.pass_state:
				self.pass_ch.invoke()
				self.pass_ent['state']='normal'
				self.pass_ent.delete(0,END)
				self.pass_ent.insert(END,'*****')
				self.pass_state=True
			else:
				self.pass_ent.delete(0,END)
				self.pass_ent.insert(END,'*****')
		else:
			if self.pass_state:
				self.pass_ch.invoke()
				self.pass_ent.delete(0,END)
				self.pass_ent['state']='disable'
				self.pass_state=False
		self.update_caps()
		
		
	def update_caps(self):
		""" обновляем списки доступности пользователя """
		self.av_caps=[]
		self.lst3.delete(0,END)
		for x in self.caps:
			self.lst3.insert(END,x)
		self.lst2.delete(0,END)
		for x in self.app.app.plugin_list:
			if x not in self.caps:
				self.av_caps.append(x)
				self.lst2.insert(END,x)
				
	def add_caps(self):
		""" кнопка добавления доступности...как еще по другому скажешь... """
		if not self.lst2.curselection():return
		sel=self.av_caps[int(self.lst2.curselection()[0])]
		self.caps.append(sel)
		self.update_caps()
	def del_caps(self):
		""" удаление доступности... ну или доступа к чему то :( """
		if not self.lst3.curselection():return	
		del self.caps[int(self.lst3.curselection()[0])]
		self.update_caps()
		
	def save_changes(self):
		""" сохраняем изменения """
		if self.pass_state:
			if not self.pass_ent.get()=='*****':
				self.passw=md5py.new(self.pass_ent.get().encode('utf-8')).hexdigest()
				
			
		else:
			self.passw=''
		self.app.app.app.db.execute('update  users set caps=? , passw=? where name=?',(repr(self.caps),self.passw,self.selected))
		self.app.app.app.con.commit()
		self.app.reload=True
		
class Sync:
	def __init__(self,app):
		""" настройки синхронизации"""
		self.app=app
		self.win=Frame(self.app.win)
		
		self.rb_var=IntVar()
		self.rb=Radiobutton(self.win,text='Отключить синхронизацию',value=0,variable=self.rb_var)
		self.rb.grid(row=0,column=0,sticky=W,padx=10,pady=10,columnspan=2)
		self.rb2=Radiobutton(self.win,text='Включить постоянно   Периодичность (мин.)',value=1,variable=self.rb_var)
		self.rb2.grid(row=1,column=0,sticky=W,padx=10,pady=10,columnspan=2)
		self.rb3=Radiobutton(self.win,text='Синхронизировать только при выходе',value=2,variable=self.rb_var)
		self.rb3.grid(row=2,column=0,sticky=W,padx=10,pady=10,columnspan=2)	
		self.cron_ent=Entry(self.win,cursor='xterm',width=3)
		self.cron_ent.grid(row=1,column=3)

		if not int(self.app.app.app.sets.sync_enable):
			self.rb_var.set(0)
			self.cron_ent.insert(END,'15')
		else:
			if int(self.app.app.app.sets.sync_period)==0:
				self.rb_var.set(2)
				self.cron_ent.insert(END,'15')
			else:
				self.rb_var.set(1)

				self.cron_ent.insert(END,self.app.app.app.sets.sync_period)
		
		self.save_but=Button(self.win,text='Сохранить',command=self.save,image=self.app.app.app.img['save'],compound='left')
		self.save_but.grid(row=10,column=0,columnspan=7,pady=20)
		
		self.frame=LabelFrame(self.win,text='Настройки текущей точки',width=300,height=250)
		self.frame.grid(padx=5,row=0,column=6,rowspan=5,sticky=N)
		Label(self.frame,text='Логин').grid(row=0,column=0,padx=5)
		self.login_ent=Entry(self.frame,width=15,cursor='xterm')
		self.login_ent.grid(row=0,column=1,pady=5)
		
		Label(self.frame,text='Пароль').grid(row=1,column=0,padx=5)
		self.passw_ent=Entry(self.frame,width=15,cursor='xterm',show='*')
		self.passw_ent.grid(row=1,column=1)		
		
		self.check_login=Button(self.frame,style='mini.TButton',text='Проверить на сервере',image=self.app.app.app.img['check'],compound='left',command=self.check_login)
		self.check_login.grid(row=0,column=2,padx=5)
		self.check_var=StringVar()
		Label(self.frame,textvariable=self.check_var,width=23,background='white').grid(row=1,column=2,padx=2)
		self.login_ent.insert(END,self.app.app.app.sets.sync_login)
		self.passw_ent.insert(END,'*****')	
		
		Label(self.frame,text='Точка',).grid(row=2,column=0,padx=2,pady=15)
		self.points_var=StringVar()
		self.points_var.set(self.app.app.app.sets.sync_point)
		self.points_ent=Combobox(self.frame,textvariable=self.points_var,state='readonly',width=15)
		self.points_ent['values']=eval(self.app.app.app.sets.sync_points)
		self.points_ent.grid(row=2,column=1)
		
		self.check_points=Button(self.frame,style='mini.TButton',text='Обновить с сервера',image=self.app.app.app.img['sync'],compound='left',command=self.check_points_from_server)		
		self.check_points.grid(row=2,column=2,padx=5)
		

	def check_points_from_server(self):
		""" проверка сохраненных точек на сервере """
		login=self.login_ent.get()
		passw=self.passw_ent.get()
		if passw=='*****':
			passw=self.app.app.app.sets.sync_passw
		else:
			passw=md5py.new(passw).hexdigest()

		self.check_var.set('Идет проверка')
		self.check_points['state']='disable'
		self.frame.update()

		d={}
		j=json.dumps({'auth':{'login':login,'passw':passw},'request':'check_points'})
		d['data']=j
		url=self.app.app.app.sets.sync_server
		try:
			response=urllib.urlopen(url+'/utils',urllib.urlencode(d)).read()
		except:
			response=None
		self.check_points['state']='normal'	
		if response:
			self.check_var.set('Обновлено')
			try:
				r=eval(response)
				self.app.app.app.sets.sync_points=repr(r)
				self.points_ent['values']=r
			except:
				self.check_var.set('Ошибка...')
				return
		else:
			self.check_var.set('Не удалось соединиться с сервером')
			



	def check_login(self):
		""" проверка правильности логина и пароля на сервере """
		login=self.login_ent.get()
		passw=self.passw_ent.get()
		if passw=='*****':
			passw=self.app.app.app.sets.sync_passw
		else:
			passw=md5py.new(passw).hexdigest()

		self.check_var.set('Идет проверка')
		self.check_login['state']='disable'
		self.frame.update()

		d={}
		j=json.dumps({'auth':{'login':login,'passw':passw},'request':'check_login'})
		d['data']=j
		url=self.app.app.app.sets.sync_server
		try:
			response=urllib.urlopen(url+'/utils',urllib.urlencode(d)).read()
		except:response='Не удалось соединиться'
		self.check_var.set(response[:50])

		self.check_login['state']='normal'
	
	def save(self):
		""" сохраняем настройки """
		s=self.rb_var.get()
		if s==0:
			self.app.app.app.sets.sync_enable=False
		elif s==2:
			self.app.app.app.sets.sync_enable=True
			self.app.app.app.sets.sync_period=0
		elif s==1:
			try:t=int(self.cron_ent.get())
			except:
				box.showerror(title='Ошибка',message='Не корректное время!')
				self.app.win.deiconify()
				return	
			if t<15:
				box.showerror(title='Ошибка',message='Время должно быть больше 15 минут!')
				self.app.win.deiconify()
				return	
			self.app.app.app.sets.sync_enable=True
			self.app.app.app.sets.sync_period=t	
		point=self.points_var.get()
		passw=self.passw_ent.get()
		if passw=='*****':
			passw=self.app.app.app.sets.sync_passw
		else:
			passw=md5py.new(passw).hexdigest()
		self.app.app.app.sets.sync_login=self.login_ent.get()
		self.app.app.app.sets.sync_passw=passw	
		self.app.app.app.sets.sync_point=point
		self.app.reload=True
		
class Updates():
	""" обновление программы """
	def __init__(self,app):
		self.app=app
		self.win=Frame(self.app.win)
		
		self.check_b=Button(self.win,text='Проверить доступные обновления',style='mini2.TButton',image=self.app.app.app.img['check'],compound='left',command=self.update_list)
		self.check_b.grid(row=0,column=0,padx=5,pady=5,sticky=N)
		



		
		self.txt=ScrolledText(self.win,width=85,height=10,font=('normal',10))
		self.txt.grid(row=1,column=0,sticky=N,padx=30)
		
		self.down_but=Button(self.win,text='Загрузить обновления',image=self.app.app.app.img['download'],compound='left',style='mini2.TButton',state='disable',command=self.download_updates)
		self.down_but.grid(row=2,column=0,pady=5)
		
	def update_list(self):
		""" загружаем список доступных обновлений """
		serv=self.app.app.app.sets.sync_server
		try:last=int(self.app.app.app.sets.last_update)
		except:last=0
		self.check_b['state']='disable'
		self.txt.delete(0.0,END)
		self.txt.insert(END,'Выполняется проверка обновлений...\n')
		self.win.update()
		data={}
		data['data']=str(last)
		try:
			resp=urllib.urlopen(serv+'/updates',urllib.urlencode(data)).read()
			resp=eval(resp)
		except Exception,x:
			self.txt.insert(END,'Не удалось подключиться к серверу обновлений :(')
			self.win.update()	
			self.check_b['state']='normal'
			return
		if len(resp)==0:
			self.txt.insert(END,'Новых обновлений не найдено!')
			self.win.update()	
			self.check_b['state']='normal'	
			return
		self.txt.delete(0.0,END)
		for x in resp:
			self.txt.insert(END,'Обновление от %s.\n%s\n\n'%(int2date(x[0]),x[1].encode('utf-8')))
		self.resp=resp
		self.down_but['state']='normal'
	def download_updates(self):
		""" загружаем сами обновления """
		serv=self.app.app.app.sets.sync_server
		self.down_but['state']='disable'
		self.win.update()
		self.txt.delete(0.0,END)
		for n,x in enumerate(self.resp):
			f=x[2]
			self.txt.insert(END,'Загрузка обновления %s из %s....\n'%(n+1,len(self.resp)))
			self.win.update()
			try:
				r=urllib.urlopen(serv+'/update_files/'+f).read()
				open('app/updates/'+f,'wb').write(r)
				if zipfile.is_zipfile('app/updates/'+f):
					self.txt.insert(END,'Успешно сохранено...\n')
				else:
					self.txt.insert(END,'Ошибка при загрузки обновления!\n')
					os.remove('app/updates/'+f)
					self.down_but['state']='normal'
					return
			except Exception,o:
				print o
				self.txt.insert(END,'Не удалось загрузить обновления...\n')
				self.down_but['state']='normal'
				return
		self.app.app.app.sets.last_update=int(time.time())
		self.txt.insert(END,'Все обновления успешно загружены. Перезапустите программу!\n')
		self.app.reload=True
			
		