#####Learning how to use Databases...############
import sqlite3

conn = sqlite3.connect('pacient.db')

c = conn.cursor()
#c.execute("""CREATE TABLE data(
 #           time real,
 #           signal real,
 #           heart real,
 #           respiratory real,
 #           saturation real,
 #           temperature real
 #           )""")
#c.execute("INSERT INTO data VALUES (0.0000,13080,79, 12, 99.99,34.6)")
#c.execute("INSERT INTO data VALUES (?,?,?,?,?,?)",(sistema.time,sistema.HS,sistema.HC,sistema.FR,sistema.OX, sistema.TM))
c.execute("INSERT INTO data VALUES (:time,:signal,:heart,:respiratory,:saturation,:temperature",
                    {time: sistema.time,signal: sistema.HS,heart: sistema.HC,respiratory: sistema.FR,saturation: sistema.OX,temperature: sistema.TM})
#c.commit()
#c.execute("SELECT * FROM data WHERE time=0.0000")
#c.fetchone()#one row
#c.fetchmany(5)#returns 5 rows
#c.fetchall()
conn.commit()
conn.close()