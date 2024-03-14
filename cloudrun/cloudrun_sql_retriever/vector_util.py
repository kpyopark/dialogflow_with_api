from pgvector.psycopg import register_vector
import psycopg
import os
from vertexai.preview.language_models import TextEmbeddingModel

class VectorDatabase():

  # Initialize the database connection
  #
  # dbname: the name of the database
  # host: the host of the database
  # port: the port of the database
  # user: the user of the database
  # password: the password of the database
  # If you don't supply dbname, host, port, user, password, the values will be extracted from the environment variables.
  # RAG_DB_NAME, RAG_DB_HOST, RAG_DB_PORT, RAG_DB_USER, RAG_DB_PASSWORD
  def __init__(self, dbname=None, host=None, port=None, user=None, password=None):
    self.model = TextEmbeddingModel.from_pretrained("textembedding-gecko-multilingual@latest")
    if dbname is None:
      dbname = os.environ['RAG_DBNAME']
    if host is None:
      host = os.environ['RAG_HOST']
    if port is None:
      port = os.environ['RAG_PORT']
    if user is None:
      user = os.environ['RAG_USER']
    if password is None:
      password = os.environ['RAG_PASSWORD']
    self.dbparams = {
      'dbname' : dbname,
      'user' : user,
      'password' : password,
      'host' : host,
      'port' : port
    }
    self.table_name = 'rag_test'
    self.create_table(self.table_name)
  
  def get_connection(self):
    conn = psycopg.connect(**self.dbparams)
    register_vector(conn)
    return conn
  
  # Create a table
  def create_table(self, table_name):
    with self.get_connection() as conn:
      try:
        with conn.cursor() as cur:
          cur.execute(f'CREATE SEQUENCE IF NOT EXISTS {table_name}_id_seq AS BIGINT START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1')
          cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id BIGINT PRIMARY KEY DEFAULT nextval('{table_name}_id_seq'), sql text, description text, parameters text, explore_view varchar(50), model_name varchar(50), table_name varchar(120), column_schema text, desc_vector vector(768))")
      except Exception as e:
        print(e)
        conn.rollback()
        raise e
      conn.commit()
  
  # Insert a row into the table
  def insert_record(self, sql, parameters, description, explore_view, model_name, table_name, column_schema, desc_vector):
    with self.get_connection() as conn:
      try:
        with conn.cursor() as cur:
          insert_record = (sql, str(description), str(parameters), explore_view, model_name, table_name, column_schema, str(desc_vector).replace(' ',''))
          cur.execute(f"INSERT INTO rag_test (sql, description, parameters, explore_view, model_name, table_name, column_schema, desc_vector) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)", insert_record) 
      except Exception as e:
        print(e)
        conn.rollback()
        raise e
      conn.commit()
  
  # Select a similar row from the table
  def select_similar_query(self, desc_vector):
    with self.get_connection() as conn:
      try:
        with conn.cursor() as cur:
          select_record = ((desc_vector,))
          cur.execute(f"SELECT sql, description, parameters, explore_view, model_name, table_name, column_schema FROM rag_test ORDER BY desc_vector <-> %s LIMIT 1", select_record)
          return cur.fetchone()
      except Exception as e:
        print(e)
        conn.rollback()
        raise e
      conn.commit()

  def find_related_tables(self, desc_vector, consine_similarity_threshold):
    results = []
    with self.get_connection() as conn:
      try:
        with conn.cursor() as cur:
          select_record = ((desc_vector, consine_similarity_threshold))
          cur.execute(f"SELECT sql, description, parameters, explore_view, model_name, table_name, column_schema FROM rag_test WHERE (1 - (desc_vector <=> %s)) < %s", select_record)
          for row in cur.fetchall():
            results.append(row)
      except Exception as e:
        print(e)
        conn.rollback()
        raise e
      conn.commit()
    return results

  def truncate_table(self):
    with self.get_connection() as conn:
      try:
        with conn.cursor() as cur:
          cur.execute(f"TRUNCATE TABLE rag_test")
      except Exception as e:
        print(e)
        conn.rollback()
        raise e
      conn.commit()