import psycopg2

conn = psycopg2.connect(
    dbname="crime_rate_h3u5",
    user="user1",
    password="BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ",
    host="dpg-d3g661u3jp1c73eg9v1g-a.render.com",
    port="5432"
)
print("Connected!")
conn.close()

