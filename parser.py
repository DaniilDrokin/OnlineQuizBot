import sqlite3
from bs4 import BeautifulSoup
import requests


DB_PATH_USER = 'db/questions1.db'
url = 'https://db.chgk.info/tour/shoikh10'
response = requests.get(url)
bs = BeautifulSoup(response.text, "lxml")
bs1 = bs.findAll('div', class_='question')
for line in bs1:
    data = line.text
    data1 = data.split(':')
    striped1 = data1[1][:-11:]
    striped2 = data1[2][:-11:]
    question = striped1.strip()
    ans = striped2.strip()
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    query = f"INSERT INTO '' (task, answer) VALUES ('{question}', '{ans}')"
    cdb.execute(query)
    db.commit()
    db.close()