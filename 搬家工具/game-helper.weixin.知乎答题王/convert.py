#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sqlite3
import traceback
import sys
import os
import json
import re
import time,datetime

'''
https://github.com/game-helper/weixin/tree/master/%E7%9F%A5%E4%B9%8E%E7%AD%94%E9%A2%98%E7%8E%8B
'''

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
                    text += x[pos:pos + offset].decode('utf-8')
                except:
                    text += '_'
                pos += offset
            return text
        except:
            try:
                return x.decode('gbk')
            except:
                pass
    return x


non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '%')


def trans(text):
    return text.translate(non_bmp_map)

def replaceText(text):
    return text.replace("'","''")


file = open("quizzes.json", "r", encoding="utf-8")
try:
#    data = ''.join(file.readlines())
    data = file.readlines()
    ret = []
    for item in data:
        item = trans(item)
        item = re.sub(r'ObjectId\(("\w+")\)', "\g<1>", item)
        item = re.sub(r'ISODate\((".+")\)', "\g<1>", item)
        ret.append(item)
    data = ''.join(ret)
except:
    traceback.print_exc()
    exit(0)
finally:
    file.close()
data = json.loads(data)

conn = sqlite3.connect('data2.db')
conn.text_factory = text_decode
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

for item in data:
    timestr = datetime.datetime.fromtimestamp(float(item['endTime'])).strftime('%Y-%m-%d %H:%M:%S')
    try:
        c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" % (replaceText(item['quiz']),timestr,'True'))
    except:
        print("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" % (replaceText(item['quiz']),timestr,'True'))
    ans=replaceText(item['options'][item['answer']-1])
    try:
        c.execute("INSERT INTO QUSTION (QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR) VALUES ('%s','%s','%s','%s','%s');" % (replaceText(item['quiz']),ans,item['school'],item['type'],replaceText(item['contributor'])))
    except:
        print("INSERT INTO QUSTION (QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR) VALUES ('%s','%s','%s','%s','%s');" % (replaceText(item['quiz']),ans,item['school'],item['type'],replaceText(item['contributor'])))
conn.commit()
