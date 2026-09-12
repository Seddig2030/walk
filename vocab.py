# -*- coding: utf-8 -*-
"""Offline-first vocabulary manager.
The 5,000 EN->AR training pairs are downloaded once from the public MUSE dictionary,
then stored locally. The app remains usable offline after that first sync.
"""
import json, os, re, threading, urllib.request
from datetime import date

MUSE_URL = "https://dl.fbaipublicfiles.com/arrival/dictionaries/en-ar.0-5000.txt"
STARTER = {
"hello":"مرحبا","goodbye":"وداعا","please":"من فضلك","thanks":"شكرا","yes":"نعم","no":"لا",
"water":"ماء","food":"طعام","home":"منزل","school":"مدرسة","teacher":"معلم","student":"طالب",
"book":"كتاب","friend":"صديق","family":"عائلة","work":"عمل","money":"مال","time":"وقت",
"day":"يوم","night":"ليل","morning":"صباح","today":"اليوم","tomorrow":"غدا","yesterday":"أمس",
"go":"يذهب","come":"يأتي","eat":"يأكل","drink":"يشرب","read":"يقرأ","write":"يكتب",
"learn":"يتعلم","study":"يدرس","speak":"يتحدث","listen":"يستمع","see":"يرى","know":"يعرف",
"want":"يريد","need":"يحتاج","like":"يحب","love":"يحب","help":"يساعد","make":"يصنع",
"take":"يأخذ","give":"يعطي","find":"يجد","look":"ينظر","use":"يستخدم","open":"يفتح",
"close":"يغلق","start":"يبدأ","finish":"ينهي","big":"كبير","small":"صغير","good":"جيد",
"bad":"سيئ","easy":"سهل","difficult":"صعب","new":"جديد","old":"قديم","happy":"سعيد",
"sad":"حزين","fast":"سريع","slow":"بطيء","important":"مهم","beautiful":"جميل","strong":"قوي",
"question":"سؤال","answer":"إجابة","example":"مثال","word":"كلمة","meaning":"معنى","language":"لغة",
"english":"الإنجليزية","arabic":"العربية","city":"مدينة","country":"دولة","world":"العالم","car":"سيارة",
"phone":"هاتف","computer":"حاسوب","internet":"إنترنت","house":"بيت","room":"غرفة","door":"باب",
"window":"نافذة","book":"كتاب","water":"ماء","air":"هواء","fire":"نار","earth":"أرض","tree":"شجرة",
"person":"شخص","people":"ناس","child":"طفل","man":"رجل","woman":"امرأة","boy":"ولد","girl":"بنت"
}

def _path(app): return os.path.join(app.user_data_dir, "vocabulary.json")

def load(app):
    path=_path(app)
    try:
        with open(path,encoding='utf-8') as f: return json.load(f)
    except Exception: return []

def save(app, data):
    os.makedirs(os.path.dirname(_path(app)),exist_ok=True)
    with open(_path(app),'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False)

def starter():
    out=[]
    for i,(en,ar) in enumerate(STARTER.items(),1):
        out.append({'id':i,'en':en,'ar':ar,'example':f'I use the word {en}.','saved':False,'written':False,'reviews':0})
    return out

def parse_muse(text):
    out=[]; seen=set()
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        parts=re.split(r'\t+',line,1)
        if len(parts)<2: parts=re.split(r'\s+',line,1)
        if len(parts)<2: continue
        en=parts[0].strip().lower(); ar=parts[1].strip()
        en=re.sub(r'[^a-zA-Z\-\' ]','',en)
        if not en or not ar or len(en)>60 or en in seen: continue
        seen.add(en)
        out.append({'id':len(out)+1,'en':en,'ar':ar,'example':f'I am learning the word {en}.','saved':False,'written':False,'reviews':0})
        if len(out)>=5000: break
    return out

def download_async(app, on_done=None):
    def work():
        ok=False; count=0; err=''
        try:
            req=urllib.request.Request(MUSE_URL,headers={'User-Agent':'WalkLearn/4.0'})
            with urllib.request.urlopen(req,timeout=35) as r: raw=r.read()
            text=raw.decode('utf-8-sig','replace')
            data=parse_muse(text)
            if len(data)>=4500:
                save(app,data); ok=True; count=len(data)
            else: err=f'البيانات المستلمة غير مكتملة ({len(data)} كلمة).'
        except Exception as e: err=str(e)
        if on_done:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt:on_done(ok,count,err),0)
    threading.Thread(target=work,daemon=True).start()

def get_words(app):
    data=load(app)
    return data if data else starter()
