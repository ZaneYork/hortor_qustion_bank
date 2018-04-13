#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sqlite3
import traceback
import sys

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

non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '_')
def trans(text):
    return text.translate(non_bmp_map)

def replaceText(text):
    if text is None:
        return ''
    return text.replace("'","''")

conn = sqlite3.connect('data.db')
conn.text_factory = text_decode
c = conn.cursor()

conn2 = sqlite3.connect('data2.db')
conn2.text_factory = text_decode
c2 = conn2.cursor()
cursor = c.execute("select QUIZ,ACCESS_TIME,IS_EXISTS from ACCESS_LOG")
log1 = {}
for row in cursor:
    if row[0] not in log1.keys():
        log1[row[0]] = []
    log1[row[0]].append((row[1], row[2]))
cursor = c2.execute("select QUIZ,ACCESS_TIME,IS_EXISTS from ACCESS_LOG")
log2 = {}
for row in cursor:
    if row[0] not in log2.keys():
        log2[row[0]] = []
    log2[row[0]].append((row[1], row[2]))
log3 = []
for quiz in log2.keys():
    if quiz not in log1.keys():
        for item in log2[quiz]:
            log3.append((quiz, item[0], item[1]))
    else:
        for item in log2[quiz]:
            if len(list(filter(lambda x: x[0] == item[0] and x[1] == item[1], log1[quiz]))) == 0:
                log3.append((quiz, item[0], item[1]))
cursor = c.execute('''
SELECT Q.QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR,ACCESS_TIME FROM QUSTION Q
LEFT JOIN (
        SELECT QUIZ,MAX(ACCESS_TIME) ACCESS_TIME FROM ACCESS_LOG GROUP BY QUIZ HAVING ACCESS_TIME = MAX(ACCESS_TIME)
) A ON Q.QUIZ like A.QUIZ;
''')
questions1 = {}
for row in cursor:
    questions1[row[0]] = (row[0], row[1], row[2], row[3], row[4], row[5])
cursor = c2.execute('''
SELECT Q.QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR,ACCESS_TIME FROM QUSTION Q
LEFT JOIN (
        SELECT QUIZ,MAX(ACCESS_TIME) ACCESS_TIME FROM ACCESS_LOG GROUP BY QUIZ HAVING ACCESS_TIME = MAX(ACCESS_TIME)
) A ON Q.QUIZ like A.QUIZ;
''')
questions2 = {}
for row in cursor:
    questions2[row[0]] = (row[0], row[1], row[2], row[3], row[4], row[5])
count_insert = 0
count_update = 0
for log in log3:
    try:
        question = questions2[log[0]]
        if log[0] in questions1.keys():
            if questions1[log[0]][5] is None or log[1] > questions1[log[0]][5]:
                c.execute("UPDATE QUSTION set OPTION='%s',SCHOOL='%s',TYPE='%s',CONTRIBUTOR='%s' where QUIZ='%s';" %
                      (trans(replaceText(question[1])), question[2], question[3], replaceText(question[4]), replaceText(question[0])))
                c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" %
                      (trans(replaceText(question[0])),log[1], 'True'))
                count_update += 1
            else:
                c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" %
                      (trans(replaceText(question[0])), log[1], 'True'))
        else:
    #        print("INSERT INTO QUSTION (QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR) VALUES ('%s','%s','%s','%s','%s');" %
    #              (trans(replaceText(question[0])), question[1], question[2], question[3], trans(replaceText(question[4]))))
            c.execute("INSERT INTO QUSTION (QUIZ,OPTION,SCHOOL,TYPE,CONTRIBUTOR) VALUES ('%s','%s','%s','%s','%s');" %
                  (trans(replaceText(question[0])), trans(replaceText(question[1])), question[2], question[3], trans(replaceText(question[4]))))
            c.execute("INSERT INTO ACCESS_LOG (QUIZ,ACCESS_TIME,IS_EXISTS) VALUES ('%s','%s','%s');" %
                  (trans(replaceText(question[0])), log[1], 'False'))
            questions1[log[0]]=(question[0], question[1], question[2], question[3], question[4], log[1])
            count_insert += 1
    except:
        print(log)
        traceback.print_exc()
conn.commit()
print("Inserted:",count_insert)
print("Updated:",count_update)
