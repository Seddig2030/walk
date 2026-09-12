# -*- coding: utf-8 -*-
__version__ = "4.0.0"
import json, os, re, random
from datetime import date, timedelta
from kivy.config import Config
Config.set('kivy','exit_on_escape','0')
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

try:
 import arabic_reshaper
 from bidi.algorithm import get_display
except Exception:
 arabic_reshaper=get_display=None

ROOT=os.path.dirname(os.path.abspath(__file__))
FONT=os.path.join(ROOT,'NotoSansArabic-Regular.ttf')
with open(os.path.join(ROOT,'curriculum.json'),encoding='utf8') as f: DATA=json.load(f)
with open(os.path.join(ROOT,'grammar.json'),encoding='utf8') as f: GRAMMAR=json.load(f)
from vocab import get_words, load as load_words, save as save_words, download_async
LESSONS=DATA['lessons']; LEVELS=DATA['levels']; LABELS=DATA['labels']
PLACEMENT=[
# --- A1 ---
('She ___ a teacher.',['is','am','are','be'],0,'A1'),
('They ___ from Jordan.',['is','am','are','was'],2,'A1'),
('I ___ two brothers.',['have','has','am','is'],0,'A1'),
('This is ___ apple.',['a','an','the','-'],1,'A1'),
# --- A2 ---
('I ___ to the market yesterday.',['go','goes','went','going'],2,'A2'),
('He ___ football every weekend.',['play','plays','playing','played'],1,'A2'),
('There ___ a lot of people in the park right now.',['is','are','was','were'],1,'A2'),
('My sister is ___ than me.',['tall','taller','tallest','more tall'],1,'A2'),
# --- B1 ---
('By the time we arrived, the film ___ already started.',['has','have','had','was'],2,'B1'),
('If I ___ more time, I would learn more.',['have','had','has','will have'],1,'B1'),
('The report ___ written by the research team.',['is','was','did','has'],1,'B1'),
('She has been living here ___ 2015.',['for','since','from','at'],1,'B1'),
# --- B2 ---
('If I ___ studied harder, I would have passed.',['have','had','has','did'],1,'B2'),
('Hardly ___ arrived when it started raining.',['I had','had I','I have','have I'],1,'B2'),
('He suggested ___ the meeting to next week.',['postpone','to postpone','postponing','postponed'],2,'B2'),
('The bridge, ___ was built in 1990, is closed for repairs.',['that','which','who','what'],1,'B2'),
# --- C1 ---
('Ostensibly is closest in meaning to:',['secretly','apparently','rarely','urgently'],1,'C1'),
('No sooner ___ the news than she called me.',['she heard','had she heard','she had heard','did she hear'],1,'C1'),
("The committee's decision was met with ___ criticism from all sides.",['scathing','mild','pleasant','minor'],0,'C1'),
('Were it not ___ his help, we would have failed.',['of','for','to','with'],1,'C1'),
]
PLACEMENT_BY_LEVEL={}
for _q in PLACEMENT: PLACEMENT_BY_LEVEL.setdefault(_q[3],[]).append(_q)
PLACEMENT_FEEDBACK={
'A1':'ابدأ بالأساسيات: التحيات، الأفعال البسيطة (to be/have)، والمفردات اليومية.',
'A2':'لديك أساس جيد. ركّز الآن على الماضي البسيط والمقارنات بين الصفات.',
'B1':'مستوى متوسط جيد. حان وقت تقوية الأزمنة المركبة (present perfect) والمبني للمجهول.',
'B2':'مستوى قوي! اعمل على الجمل الشرطية المتقدمة وأسلوب الانعكاس اللغوي (inversion).',
'C1':'مستوى متقدم ممتاز! ركّز على المفردات الدقيقة والأسلوب الأكاديمي لتصل لطلاقة الناطقين.',
}

def ar(s):
 if not isinstance(s,str): return str(s)
 if arabic_reshaper and get_display and any('\u0600'<=c<='\u06ff' for c in s):
  try:return get_display(arabic_reshaper.reshape(s))
  except:pass
 return s

def speak(text,slow=False):
 try:
  from jnius import autoclass
  A=autoclass('org.kivy.android.PythonActivity'); T=autoclass('android.speech.tts.TextToSpeech'); L=autoclass('java.util.Locale')
  app=App.get_running_app()
  if not hasattr(app,'tts'): app.tts=T(A.mActivity,None)
  app.tts.setLanguage(L.US); app.tts.setSpeechRate(0.55 if slow else 0.9); app.tts.speak(text,T.QUEUE_FLUSH,None,'walklearn')
 except Exception: pass

def ppath(): return os.path.join(App.get_running_app().user_data_dir,'progress.json')
def progress():
 d={'level':None,'completed':[],'streak':0,'last':None,'xp':0,'saved_words':[],'written_words':[]}
 try:
  with open(ppath(),encoding='utf8') as f:d.update(json.load(f))
 except: pass
 return d

def savep(d):
 os.makedirs(os.path.dirname(ppath()),exist_ok=True)
 with open(ppath(),'w',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2)

def award(xp=0):
 d=progress(); d['xp']+=xp; today=date.today().isoformat()
 if d['last']!=today:
  yesterday=(date.today()-timedelta(days=1)).isoformat(); d['streak']=d['streak']+1 if d['last']==yesterday else 1; d['last']=today
 savep(d)
 return d

def finish_lesson(lid,score):
 d=progress()
 if lid not in d['completed']: d['completed'].append(lid); d['xp']+=50+score*10
 today=date.today().isoformat()
 if d['last']!=today:
  y=(date.today()-timedelta(days=1)).isoformat(); d['streak']=d['streak']+1 if d['last']==y else 1; d['last']=today
 savep(d)

class Base(Screen):
 def shell(self):
  root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(7)); scroll=ScrollView(do_scroll_x=False); c=BoxLayout(orientation='vertical',spacing=dp(7),size_hint_y=None); c.bind(minimum_height=c.setter('height')); scroll.add_widget(c); root.add_widget(scroll); return root,c
 def label(self,c,text,size=16):
  w=Label(text=ar(text),font_name=FONT if os.path.exists(FONT) else 'Roboto',font_size=f'{size}sp',color=(.95,.95,.97,1),halign='right',valign='middle',text_size=(Window.width-dp(28),None),size_hint_y=None)
  w.bind(texture_size=lambda i,v:setattr(i,'height',v[1]+dp(10))); c.add_widget(w); return w
 def button(self,c,text,fn,primary=False):
  b=Button(text=ar(text),font_name=FONT if os.path.exists(FONT) else 'Roboto',font_size='15sp',size_hint_y=None,height=dp(48),background_normal='',background_color=(.86,.62,.12,1) if primary else (.12,.13,.16,1),color=(.05,.05,.05,1) if primary else (.95,.95,.95,1)); b.bind(on_release=lambda *_:fn()); c.add_widget(b); return b
 def nav(self,c):
  self.button(c,'⌂ الرئيسية',lambda:setattr(self.manager,'current','dashboard'))

class Landing(Base):
 def on_pre_enter(self):
  self.clear_widgets(); r,c=self.shell(); self.label(c,'WALKLEARN',30); self.label(c,'تطبيق متكامل لتعلم الإنجليزية من A1 إلى C1',20); self.label(c,'قواعد + أكثر من 5000 كلمة إنجليزية مترجمة + حفظ + كتابة + نطق + مراجعة + اختبارات.',16)
  self.button(c,'ابدأ اختبار تحديد المستوى الذكي',lambda:setattr(self.manager,'current','placement'),True); self.button(c,'أدخل مباشرة للتعلم',self.direct); self.label(c,'اختبار تكيّفي يغطي A1 حتى C1 مع تقرير أداء مفصّل.',13); self.label(c,'المفردات الكبيرة تُحمّل مرة واحدة ثم تعمل من الهاتف بدون إنترنت.',13); self.add_widget(r)
 def direct(self):
  d=progress(); d['level']=d['level'] or 'A1'; savep(d); self.manager.current='dashboard'

class Placement(Base):
 def on_pre_enter(self): self.level_idx=0; self.qi=0; self.breakdown={}; self.passed=[]; self.render()
 def qs(self): return PLACEMENT_BY_LEVEL.get(LEVELS[self.level_idx],[])
 def render(self):
  self.clear_widgets(); r,c=self.shell(); lvl=LEVELS[self.level_idx]; qs=self.qs()
  if self.qi>=len(qs): self.finish_level(); return
  q=qs[self.qi]
  self.label(c,f'اختبار تحديد المستوى — {lvl} ({self.qi+1}/{len(qs)})',14); self.label(c,q[0],21)
  for i,o in enumerate(q[1]): self.button(c,o,lambda i=i:self.answer(i))
  self.add_widget(r)
 def answer(self,i):
  qs=self.qs(); q=qs[self.qi]; lvl=LEVELS[self.level_idx]; ok=i==q[2]
  entry=self.breakdown.setdefault(lvl,[0,0]); entry[1]+=1; entry[0]+= 1 if ok else 0
  self.qi+=1; self.render()
 def finish_level(self):
  lvl=LEVELS[self.level_idx]; correct,total=self.breakdown.get(lvl,[0,0])
  passed=total>0 and correct/total>=0.5
  if passed: self.passed.append(lvl)
  if not passed or self.level_idx==len(LEVELS)-1: self.conclude(); return
  self.level_idx+=1; self.qi=0; self.render()
 def conclude(self):
  final=self.passed[-1] if self.passed else 'A1'
  d=progress(); d['level']=final; savep(d)
  self.manager.get_screen('placementresult').start(final,self.breakdown); self.manager.current='placementresult'

class PlacementResult(Base):
 def start(self,level,breakdown): self.level=level; self.breakdown=breakdown; self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell()
  self.label(c,'🎯 نتيجة تحديد المستوى',27)
  self.label(c,f'مستواك: {LABELS.get(self.level,self.level)} ({self.level})',22)
  self.label(c,PLACEMENT_FEEDBACK.get(self.level,''),16)
  self.label(c,'تفاصيل الأداء حسب المستوى:',17)
  for lv in LEVELS:
   if lv in self.breakdown:
    correct,total=self.breakdown[lv]; pct=int(100*correct/total) if total else 0
    self.label(c,f'{lv}: {correct}/{total} صحيح ({pct}%)',14)
  self.button(c,'متابعة إلى اللوحة',lambda:setattr(self.manager,'current','dashboard'),True)
  self.button(c,'إعادة اختبار المستوى',lambda:setattr(self.manager,'current','placement'))
  self.add_widget(r)

class Dashboard(Base):
 def on_pre_enter(self): self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); d=progress(); lvl=d['level'] or 'A1'; self.label(c,'لوحة التعلم',27); self.label(c,f'مستواك الحالي: {LABELS.get(lvl,lvl)} ({lvl})',19); self.label(c,f"🔥 السلسلة: {d['streak']} يوم    ⭐ XP: {d['xp']}",15)
  ls=[x for x in LESSONS if x['level']==lvl]; done=sum(x['id'] in d['completed'] for x in ls); self.label(c,f'الدروس المكتملة في مستواك: {done}/{len(ls)}',15)
  words=load_words(App.get_running_app()); saved=len(d['saved_words']); self.label(c,f'📚 قاموسك: {len(words)} كلمة متاحة الآن    ❤️ محفوظ: {saved}',15)
  self.button(c,'📖 المفردات 5000+',lambda:setattr(self.manager,'current','vocab'),True); self.button(c,'📘 القواعد الإنجليزية',lambda:setattr(self.manager,'current','grammar')); self.button(c,'🎓 الدروس',lambda:setattr(self.manager,'current','lessons')); self.button(c,'📊 تقدمي',lambda:setattr(self.manager,'current','progress')); self.add_widget(r)

class Vocab(Base):
 def on_pre_enter(self): self.query=''; self.data=get_words(App.get_running_app()); self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); self.label(c,'📚 قاموس WalkLearn — 5000+ كلمة',25); self.label(c,f'عدد الكلمات المحملة: {len(self.data)}',14)
  inp=TextInput(text=self.query,multiline=False,hint_text='ابحث بالإنجليزية أو العربية',size_hint_y=None,height=dp(52),font_size='18sp'); c.add_widget(inp)
  def search(): self.query=inp.text.strip().lower(); self.render()
  self.button(c,'🔎 بحث',search,True)
  if len(self.data)<4500:
   self.label(c,'النسخة تعمل الآن بقاموس بداية صغير. اضغط تنزيل 5000 كلمة لتحميل القاموس الكامل مرة واحدة.',14)
   self.button(c,'⬇️ تنزيل 5000 كلمة مترجمة',self.download,True)
  d=progress(); saved=set(d['saved_words']); q=self.query
  shown=[w for w in self.data if not q or q in w['en'].lower() or q in w['ar']][:80]
  for w in shown:
   mark=' ❤️' if w['en'] in saved else ''; self.button(c,f"{w['en']} — {w['ar']}{mark}",lambda w=w:self.open_word(w))
  self.nav(c); self.add_widget(r)
 def download(self):
  self.label # keep class alive
  def done(ok,count,err):
   if ok: self.data=load_words(App.get_running_app()); self.render()
   else:
    # show a compact status screen via a temporary popup-like label on refresh
    self.query=''; self.render(); self._status=err
  download_async(App.get_running_app(),done)
  self.clear_widgets(); r,c=self.shell(); self.label(c,'جاري تنزيل قاموس 5000 كلمة...',23); self.label(c,'اترك التطبيق مفتوحاً واتصل بالإنترنت. بعد اكتمال التنزيل سيعمل القاموس دون اتصال.',15); self.nav(c); self.add_widget(r)
 def open_word(self,w): self.manager.get_screen('word').start(w); self.manager.current='word'

class Word(Base):
 def start(self,w): self.w=w; self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); w=self.w; d=progress(); saved=w['en'] in d['saved_words']; written=w['en'] in d['written_words']; self.label(c,'الكلمة',14); self.label(c,w['en'],32); self.label(c,w['ar'],23); self.label(c,w.get('example',''),17); self.label(c,'معناها: '+w['ar'],15)
  self.button(c,'🔊 نطق طبيعي',lambda:speak(w['en'])); self.button(c,'🐢 نطق بطيء',lambda:speak(w['en'],True)); self.button(c,'❤️ حفظ الكلمة' if not saved else '💔 إزالة الحفظ',self.toggle,True); self.button(c,'✍️ تدريب الكتابة',self.write); self.nav(c); self.add_widget(r)
 def toggle(self):
  d=progress(); arr=set(d['saved_words']); arr.remove(self.w['en']) if self.w['en'] in arr else arr.add(self.w['en']); d['saved_words']=sorted(arr); d['xp']+=2; savep(d); self.render()
 def write(self): self.manager.get_screen('writeword').start(self.w); self.manager.current='writeword'

class WriteWord(Base):
 def start(self,w): self.w=w; self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); self.label(c,'✍️ اكتب الكلمة',25); self.label(c,'اكتب الكلمة الإنجليزية التي تعني:',15); self.label(c,self.w['ar'],25); inp=TextInput(multiline=False,halign='center',font_size='23sp',size_hint_y=None,height=dp(56)); c.add_widget(inp); msg=self.label(c,'',15)
  def check():
   if inp.text.strip().lower()==self.w['en'].lower(): msg.text=ar('صحيح ✓'); msg.color=(.4,.95,.65,1); d=progress();
   else: msg.text=ar('الصحيح: '+self.w['en']); msg.color=(1,.45,.4,1)
   if inp.text.strip().lower()==self.w['en'].lower():
    d=progress(); s=set(d['written_words']); s.add(self.w['en']); d['written_words']=sorted(s); d['xp']+=5; savep(d)
  self.button(c,'تحقق',check,True); self.button(c,'🔊 اسمع الكلمة',lambda:speak(self.w['en'])); self.nav(c); self.add_widget(r)

class Grammar(Base):
 def on_pre_enter(self): self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); self.label(c,'📘 قواعد الإنجليزية',27); self.label(c,'32 درساً من الأساسيات إلى C1.',14)
  for g in GRAMMAR:self.button(c,f"{g['level']} — {g['title']} — {g['ar']}",lambda g=g:self.open(g))
  self.nav(c); self.add_widget(r)
 def open(self,g): self.manager.get_screen('gramdetail').start(g); self.manager.current='gramdetail'

class GramDetail(Base):
 def start(self,g): self.g=g; self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); g=self.g; self.label(c,f"{g['level']} — {g['title']}",26); self.label(c,g['ar'],19); self.label(c,g['rule'],16)
  for en,arx in g['examples']:
   self.label(c,en,18); self.label(c,arx,14); self.button(c,'🔊 نطق المثال',lambda en=en:speak(en))
  self.button(c,'رجوع للقواعد',lambda:setattr(self.manager,'current','grammar')); self.add_widget(r)

class Lessons(Base):
 def on_pre_enter(self): self.lvl=progress()['level'] or 'A1'; self.render()
 def render(self):
  self.clear_widgets(); r,c=self.shell(); self.label(c,'🎓 الدروس',26); self.label(c,f'المستوى المختار: {self.lvl}',15)
  for lv in LEVELS:self.button(c,lv,lambda lv=lv:self.choose(lv))
  d=progress()
  for l in [x for x in LESSONS if x['level']==self.lvl]: self.button(c,(('✓ ' if l['id'] in d['completed'] else '')+l['titleAr']),lambda l=l:self.open(l))
  self.nav(c); self.add_widget(r)
 def choose(self,lv):self.lvl=lv;self.render()
 def open(self,l):self.manager.get_screen('lesson').start(l);self.manager.current='lesson'

class Lesson(Base):
 def start(self,l):self.lesson=l;self.stage='vocab';self.i=0;self.li=0;self.qi=0;self.score=0;self.queue=list(range(len(l['vocab'])));self.revealed=False;self.render()
 def render(self):
  self.clear_widgets();r,c=self.shell();self.label(c,self.lesson['titleAr'],24)
  if self.stage=='vocab':self.vocab(c)
  elif self.stage=='memorize':self.memorize(c)
  elif self.stage=='writing':self.writing(c)
  elif self.stage=='listening':self.listening(c)
  elif self.stage=='grammar':self.grammar(c)
  elif self.stage=='reading':self.reading(c)
  elif self.stage=='quiz':self.quiz(c)
  else:self.done(c)
  self.nav(c);self.add_widget(r)
 def vocab(self,c):
  for v in self.lesson['vocab']:self.label(c,f"{v['en']} — {v['ar']}",18);self.label(c,v['example'],13);self.button(c,'🔊 نطق',lambda t=v['en']:speak(t))
  self.button(c,'التالي: الحفظ',lambda:self.setstage('memorize'),True)
 def memorize(self,c):
  if not self.queue:self.button(c,'التالي: الكتابة',lambda:self.setstage('writing'),True);return
  v=self.lesson['vocab'][self.queue[0]];self.label(c,f'باقي {len(self.queue)} كلمة',13);self.label(c,v['ar'],24)
  if self.revealed:self.label(c,v['en'],28);self.button(c,'🔊 اسمع',lambda:speak(v['en']));self.button(c,'حفظتها ✓',self.remember,True);self.button(c,'أعدها',self.repeat)
  else:self.button(c,'👁 اكشف',lambda:self.reveal(),True)
 def reveal(self):self.revealed=True;self.render()
 def remember(self):self.queue.pop(0);self.revealed=False;self.render()
 def repeat(self):self.queue.append(self.queue.pop(0));self.revealed=False;self.render()
 def writing(self,c):
  v=self.lesson['vocab'][self.i];self.label(c,f'كتابة {self.i+1}/{len(self.lesson["vocab"])}',13);self.label(c,'اكتب الإنجليزية لـ: '+v['ar'],19);inp=TextInput(multiline=False,halign='center',font_size='21sp',size_hint_y=None,height=dp(54));c.add_widget(inp);msg=self.label(c,'',14);checked=[False]
  def go():
   if not checked[0]:msg.text=ar('الصحيح: '+v['en']) if inp.text.strip().lower()!=v['en'].lower() else ar('صحيح ✓');checked[0]=True;btn.text=ar('التالي');return
   self.i+=1;self.setstage('listening') if self.i>=len(self.lesson['vocab']) else self.render()
  btn=self.button(c,'تحقق',go,True)
 def listening(self,c):
  vocab=self.lesson['vocab']
  if len(vocab)<2 or self.li>=len(vocab):self.setstage('grammar');return
  v=vocab[self.li]; pool=[w['en'] for w in vocab if w['en']!=v['en']]; random.shuffle(pool)
  opts=[v['en']]+pool[:3]; random.shuffle(opts); picked=[False]
  self.label(c,f'استماع {self.li+1}/{len(vocab)}',13); self.label(c,'استمع جيداً ثم اختر الكلمة الصحيحة',17)
  self.button(c,'🔊 تشغيل الصوت',lambda:speak(v['en']),True); msg=self.label(c,'',14)
  def pick(o):
   if picked[0]:return
   picked[0]=True; ok=o==v['en']
   msg.text=ar('صحيح ✓') if ok else ar('الصحيح: '+v['en']); msg.color=(.4,.95,.65,1) if ok else (1,.45,.4,1)
   if ok:d=progress();d['xp']+=3;savep(d)
   Clock.schedule_once(lambda dt:self.advance_listening(),0.9)
  for o in opts:self.button(c,o,lambda o=o:pick(o))
  Clock.schedule_once(lambda dt:speak(v['en']),0.4)
 def advance_listening(self):self.li+=1;self.render()
 def grammar(self,c):
  self.label(c,self.lesson['grammarTitleAr'],19);self.label(c,self.lesson['grammarNoteAr'],15)
  for e in self.lesson['grammarExamples']:self.label(c,e['en'],17);self.label(c,e['ar'],13);self.button(c,'🔊',lambda t=e['en']:speak(t))
  self.button(c,'التالي: القراءة',lambda:self.setstage('reading'),True)
 def reading(self,c):
  r=self.lesson.get('reading')
  if not r:
   texts=[v.get('example','') for v in self.lesson['vocab'] if v.get('example')]
   textsAr=[v.get('exampleAr','') for v in self.lesson['vocab'] if v.get('exampleAr')]
   r={'titleAr':'نص قرائي: '+self.lesson['titleAr'],'en':' '.join(texts),'ar':' '.join(textsAr)}
  self.label(c,r['titleAr'],19);self.label(c,r['en'],16);self.label(c,r['ar'],14);self.button(c,'🔊 استمع للنص',lambda:speak(r['en']));self.button(c,'التالي: الاختبار',lambda:self.setstage('quiz'),True)
 def quiz(self,c):
  q=self.lesson['quiz'][self.qi];self.label(c,f'اختبار {self.qi+1}/{len(self.lesson["quiz"])}',13);self.label(c,q['promptAr'],18)
  for i,o in enumerate(q['options']):self.button(c,o,lambda i=i:self.answer(i))
 def answer(self,i):self.score+=i==self.lesson['quiz'][self.qi]['answerIndex'];self.qi+=1;self.setstage('done') if self.qi>=len(self.lesson['quiz']) else self.render()
 def done(self,c):self.label(c,'🎉 أحسنت!',28);self.label(c,f'النتيجة {self.score}/{len(self.lesson["quiz"])}',20);self.button(c,'حفظ التقدم',self.finish,True)
 def finish(self):finish_lesson(self.lesson['id'],self.score);self.manager.current='lessons'
 def setstage(self,s):self.stage=s;self.render()

class Progress(Base):
 def on_pre_enter(self):self.render()
 def render(self):
  self.clear_widgets();r,c=self.shell();d=progress();words=load_words(App.get_running_app());self.label(c,'📊 تقدمي',27);self.label(c,f"المستوى: {d['level'] or 'غير محدد'}",17);self.label(c,f"🔥 السلسلة: {d['streak']} يوم",15);self.label(c,f"⭐ XP: {d['xp']}",15);self.label(c,f"الدروس: {len(d['completed'])}/{len(LESSONS)}",15);self.label(c,f"الكلمات المحفوظة: {len(d['saved_words'])}",15);self.label(c,f"الكلمات التي تدربت على كتابتها: {len(d['written_words'])}",15);self.label(c,f"قاموس الجهاز: {len(words)} كلمة",15);self.button(c,'إعادة ضبط التقدم',self.reset);self.nav(c);self.add_widget(r)
 def reset(self):savep({'level':None,'completed':[],'streak':0,'last':None,'xp':0,'saved_words':[],'written_words':[]});self.render()

class WalkLearn(App):
 def build(self):
  Window.clearcolor=(.035,.035,.045,1);sm=ScreenManager()
  for cls,name in [(Landing,'landing'),(Placement,'placement'),(PlacementResult,'placementresult'),(Dashboard,'dashboard'),(Vocab,'vocab'),(Word,'word'),(WriteWord,'writeword'),(Grammar,'grammar'),(GramDetail,'gramdetail'),(Lessons,'lessons'),(Lesson,'lesson'),(Progress,'progress')]:sm.add_widget(cls(name=name))
  sm.current='dashboard' if progress()['level'] else 'landing';return sm
if __name__=='__main__':WalkLearn().run()
