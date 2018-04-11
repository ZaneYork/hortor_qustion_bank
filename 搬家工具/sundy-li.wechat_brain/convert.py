#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sqlite3
import traceback
import sys
import os
import json
import time

'''
https://github.com/sundy-li/wechat_brain
'''
file = open("a.txt", "r", encoding="utf-8")
try:
    data = file.readlines()
except:
    traceback.print_exc()
    exit(0)
finally:
    file.close()
questions={}
tmp_qus = None
for i in range(0,len(data)):
    item = data[i].split('=')
    if len(item) > 1:
        if tmp_qus is not None:
            item[0] = '%s\n%s'%(tmp_qus,item[0])
            tmp_qus = None
        try:
            questions[item[0]] = json.loads("=".join(item[1:]))
        except:
            pass
    else:
        x = input(data[i] + "[Q/A]?")
        if x == "A":
            lastitem = data[i-1].split('=')
            questions.pop(lastitem[0])
            ans = '%s\n%s'%("=".join(lastitem[1:]),item[0])
            questions[lastitem[0]] = json.loads(ans)
            print(lastitem[0],ans)
        else:
            tmp_qus = item[0]

def text_decode(x):
    try:
        return x.decode('utf-8')
    except UnicodeDecodeError as e:
        try:
            pos = int(e.start)
            text = x[0:pos].decode('utf-8')
            offset = 0
            while(pos < len(x)):
                if x[pos] > 0xe0:
                    offset = 3
                elif x[pos] > 0xc0:
                    offset = 2
                else:
                    offset = 1
                try:
                    text+=x[pos:pos+offset].decode('utf-8')
                except:
                    text+='_'
                pos+=offset
            return text
        except:
            try:
                return x.decode('gbk')
            except:
                pass
    return x

non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '_')
def trans(text):
    return text.translate(non_bmp_map)

conn = sqlite3.connect('data.db')
conn.text_factory=text_decode
c = conn.cursor()
try:
    c.execute('''
CREATE TABLE
    QUSTION
    (
        QUIZ TEXT NOT NULL,
        OPTION TEXT NOT NULL,
        SCHOOL TEXT,
        TYPE TEXT,
        CONTRIBUTOR TEXT,
        PRIMARY KEY (QUIZ)
    );''')
    conn.commit()
except:
    pass

try:
    c.execute('''
CREATE TABLE
    ACCESS_LOG
    (
        IDX INTEGER,
        QUIZ TEXT NOT NULL,
        ACCESS_TIME TEXT,
        IS_EXISTS TEXT,
        PRIMARY KEY (IDX)
    );''')
    conn.commit()
except:
    pass

cursor = c.execute('''
SELECT Q.QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR,ACCESS_TIME FROM QUSTION Q
LEFT JOIN (
        SELECT QUIZ,MAX(ACCESS_TIME) ACCESS_TIME FROM ACCESS_LOG GROUP BY QUIZ HAVING ACCESS_TIME = MAX(ACCESS_TIME)
) A ON Q.QUIZ like A.QUIZ;
''')
questions1 = {}
for row in cursor:
    questions1[row[0].replace('_','')] = (row[0], row[1], row[2], row[3], row[4], row[5])

def replaceText(text):
    return text.replace("'","''")

count_insert = 0
count_update = 0
for key in questions.keys():
    decodedKey = trans(key).replace('_','')
    question=(questions[key]['a'],questions[key]['ts'])
    timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(question[1]))
    if decodedKey not in questions1.keys():
        print(decodedKey)
        c.execute("INSERT INTO QUSTION (QUIZ,OPTION) VALUES ('%s','%s');" %
              (replaceText(key), replaceText(question[0])))
        c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" %
              (trans(replaceText(key)), timestr, 'False'))
        count_insert += 1
    elif questions1[decodedKey][5] is None or timestr > questions1[decodedKey][5]:
        if question[1] != 0:
            pass
#            c.execute("UPDATE QUSTION set OPTION='%s' where QUIZ='%s';" %
#                    (replaceText(question[0]), replaceText(key)))
#            c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" %
#                    (trans(replaceText(key)),timestr, 'True'))
#            count_update += 1
conn.commit()
print("Inserted:",count_insert)
print("Updated:",count_update)
