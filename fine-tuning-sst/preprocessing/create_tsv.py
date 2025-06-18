# This script will export train.tsv file to each set directory

import sqlite3
import csv
import os

path = "set_3"

conn = sqlite3.connect(os.path.join(path, "database.db"))
cursor = conn.cursor()

cursor.execute("SELECT audioText, text FROM NewGatheredText WHERE isCheck = 0")
rows = cursor.fetchall()


rows = [list(row) for row in rows]
for i in range(len(rows)):
    rows[i][0] = rows[i][0].replace("internal/repository/successful_clips/", "")
    rows[i][0] = rows[i][0].replace("internal/repository/wait_clips/", "")


with open(os.path.join(path, "train.tsv"), "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["path", "sentence"])
    writer.writerows(rows)

conn.close()
