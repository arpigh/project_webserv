##Веб-сервис: обратиться через API VK к заданному набору сообществ, скачать записи за определённый период 
##и построить графики частотности ключевых для тематки сообщества слов (для сообществ, посвящённым фильмам, 
##"режиссёр", "кино", "премьера", "показ", "блокбастер", остальные найти через семантические вектора)

import numpy
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, request, render_template
import flask
import gensim 
import codecs
import numpy
import datetime 
import urllib.request  
import json
import matplotlib.pyplot as plt
import re
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()

def get_text(group_id): ##функция, выгружающся 200 текстов из заданной группы 
    req = urllib.request.Request('https://api.vk.com/method/wall.get?owner_id=-' + group_id + '&count=100&v=5.74&access_token=8423c2448423c2448423c244d08441f2a1884238423c244dee1644d9e90529494134bf8') 
    response = urllib.request.urlopen(req) 
    result = response.read().decode('utf-8')
    req1 = urllib.request.Request('https://api.vk.com/method/wall.get?owner_id=-' + group_id + '&count=100&offset=100&v=5.74&access_token=8423c2448423c2448423c244d08441f2a1884238423c244dee1644d9e90529494134bf8') 
    response = urllib.request.urlopen(req1) 
    result1 = response.read().decode('utf-8')
    data1 = json.loads(result)
    data2 = json.loads(result1)
    data=dict()
    data.update(data1)
    data=data1['response']['items']+data2['response']['items']
    texts = []
    for i in range(len(data)):
        if data[i]['text'] != '':
            texts.append(data[i]['text'])
    return texts

def prep(texts): ##предобработка тестов   
    prep_txts = []
    for txt in texts:
        txt=  re.sub('[^а-я|\s|А-Я]', '', txt) #удаляем из предожения все, кроме букв и пробелов
        txt = txt.lower()
        prep_txts.append(txt)
        
    return prep_txts

ch_r = ['NPRO','PRED','PREP','CONJ','PRCL','INTJ'] #части речи , которые не учитываются (служебные)
def words_lst(texts): ##разбиение на слова в н.ф.
    words_l = []
    for txt in texts:
        for word in txt.split():
            lem = morph.parse(word)[0]
            if lem.tag.POS not in ch_r: #если нет в списке ch_r берем 
                words_l.append(lem.normal_form)
    return words_l

def freq_dict(words): #составление словая частотности для слов
    d = {}
    for word in words:
        try:
            d[word] += 1   
        except:
            d[word] = 1      
    return d

words_ = ["режиссёр_NOUN", "кино_NOUN", "премьера_NOUN", "показ_NOUN", "блокбастер_NOUN"]

m = 'ruscorpora_upos_skipgram_300_5_2018.vec.gz' ##загружаем модель word2vec
if m.endswith('.vec.gz'):
    model = gensim.models.KeyedVectors.load_word2vec_format(m, binary=False)
elif m.endswith('.bin.gz'):
    model = gensim.models.KeyedVectors.load_word2vec_format(m, binary=True)
else:
    model = gensim.models.KeyedVectors.load(m)

model.init_sims(replace=True)

#первые 4 ближайшие по косинусовой схожести слов, берем в словарь 
dop_words = []
for  word  in  words_:
    if word in model:
        for i in model.most_similar(positive=[word], topn=4):
            # слово + коэффициент косинусной близости
            wrd =  re.sub('[^а-я|\s|А-Я]', '',  i[0])
            wrd = morph.parse(wrd)[0].normal_form
            dop_words.append(wrd)

words_ = ["режиссёр", "кино", "премьера", "показ", "блокбастер"]
words_  = dop_words + words_
def for_bar_dict(fr_dict):#словарь для постоение столбчатой диаграммы
    graph_dict = {}
    for word in words_:    
        try:
            graph_dict[word] = fr_dict[word] 
        except:
            graph_dict[word] = 0
    return  graph_dict

empty_lab = ['' for wrd in words_]
app = Flask(__name__)

@app.route('/')
def hello_world():   

    return render_template('ind.html', words = dop_words) 
   

@app.route('/serv')
def serv():
    param = request.args
    try: 
        texts1 = get_text(param['first'])
        texts2 = get_text(param['second'])
        texts3 = get_text(param['third'])
        
    except:
        return 'Ошибка!<p>Вернуться на главную страницу:</p>  <form action="/">                     <p><input type="submit" value = "на главную"></p>'

    texts2 = prep(texts2)
    words2 = words_lst(texts2)
    fr_dict2 = freq_dict(words2)

    texts1 = prep(texts1)
    words1 = words_lst(texts1)
    fr_dict1 = freq_dict(words1)

    texts3 = prep(texts3)
    words3 = words_lst(texts3)
    fr_dict3 = freq_dict(words3)

    words = words3 + words2 + words1
    fr_dict = freq_dict(words)

    words = words3 + words2 + words1
    fr_dict = freq_dict(words)
    
    graph_dict = for_bar_dict(fr_dict) #кол-во повтерий слов - слова во всем корпусе
    graph_dict1 = for_bar_dict(fr_dict1)#кол-во повтерий слов - слова в первой группе
    graph_dict2 = for_bar_dict(fr_dict2)#кол-во повтерий слов - слова во второй группе
    graph_dict3 = for_bar_dict(fr_dict3)#кол-во повтерий слов - слова в третей группе

    #строим графики
    plt.figure(1, figsize = (20,15))

    plt.subplot(221)
    plt.bar(range(len(graph_dict.keys())), graph_dict.values(), color  = 'red')
    plt.ylabel('Количество повторений слова')
    plt.xticks(range(len(graph_dict.keys())),empty_lab, rotation=90)
    plt.title('Частотность слов по всему корпусу')

    plt.subplot(222)
    plt.bar(range(len(graph_dict1.keys())), graph_dict1.values(), color  = 'g')
    plt.ylabel('Количество повторений слова')
    plt.xticks(range(len(graph_dict1.keys())),empty_lab, rotation=90)
    plt.title('Частотность слов группы номер 1')

    plt.subplot(223)
    plt.bar(range(len(graph_dict2.keys())), graph_dict2.values(), color  = 'g')
    plt.ylabel('Количество повторений слова')
    plt.xlabel('Слова')
    plt.xticks(range(len(graph_dict2.keys())), graph_dict2.keys(), rotation=90)
    plt.title('Частотность слов группы номер 2')

    plt.subplot(224)
    plt.bar(range(len(graph_dict3.keys())), graph_dict3.values(), color  = 'g')
    plt.ylabel('Количество повторений слова')
    plt.xlabel('Слова')
    plt.xticks(range(len(graph_dict3.keys())), graph_dict3.keys(), rotation=90)
    plt.title('Частотность слов группы номер 3')
    
    
    #сохраняем график для вывода в веб
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue()).decode('ascii')
    
    return render_template('output.html', result=figdata_png)  

if __name__ == "__main__":
    app.run()

