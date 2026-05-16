import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_DIRECT_URL'])
print('✅ DB connection successful')
conn.close()