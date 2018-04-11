#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sqlite3
import traceback
import sys
import os
import json
import time
'''
https://github.com/wansir/tounao
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


conn = sqlite3.connect('data.db')
conn.text_factory = text_decode
c = conn.cursor()

conn2 = sqlite3.connect('data2.db')
conn2.text_factory = text_decode
c2 = conn2.cursor()
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
    questions1[row[0]] = (row[0], row[1], row[2], row[3], row[4], row[5])

cursor = c2.execute('''select quiz,answer,school,type from questions;''')
questions2 = {}
for row in cursor:
    questions2[row[0]] = (row[1], row[2], row[3])


def replaceText(text):
    return text.replace("'", "''")

count_insert = 0
count_update = 0
for key in questions2.keys():
    question = questions2[key]
    if key not in questions1.keys():
        c.execute("INSERT INTO QUSTION (QUIZ,OPTION,SCHOOL,TYPE) VALUES ('%s','%s','%s','%s');" %
                  (replaceText(key), replaceText(question[0]), question[1], question[2]))
        count_insert += 1
    elif questions1[key][2] is None:
        if question[2] is not None and question[2] != 'nil':
            c.execute("UPDATE QUSTION set SCHOOL='%s',TYPE='%s' where QUIZ='%s';" %
                      (question[1], question[2], replaceText(key)))
            count_update += 1
conn.commit()
print("Inserted:",count_insert)
print("Updated:",count_update)
