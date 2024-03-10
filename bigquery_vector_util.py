from typing import List
from google.cloud import bigquery
import os
import json


class SqlSearchSchema:

  def __init__(self, sql, parameters, description, explore_view, model_name, table_name, column_schema, desc_vector):
    self.sql = sql
    self.parameters = parameters
    self.description = description
    self.explore_view = explore_view
    self.model_name = model_name
    self.table_name = table_name
    self.column_schema = column_schema
    self.desc_vector = desc_vector

  def to_dict(self):
    return {
      'sql': self.sql,
      'description': self.description,
      'parameters': self.parameters,
      'explore_view': self.explore_view,
      'model_name': self.model_name,
      'table_name': self.table_name,
      'column_schema': self.column_schema,
      'desc_vector': self.desc_vector
    }

class BigQueryVectorDatabase():

  def __init__(self, project_id, location, dataset, table_name):
    self.dataset = dataset
    self.table_name = table_name
    self.project_id = project_id
    self.location = location
    self.bigquery_client = bigquery.Client(project=self.project_id, location=self.location)
    self.table_ref = self.bigquery_client.dataset(self.dataset).table(self.table_name)

  # Create a table in BigQuery)

  def create_table(self):
    query = self.bigquery_client.query(
      """CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.{table_name}` (
        uuid STRING DEFAULT GENERATE_UUID(), 
        sql STRING, 
        description STRING, 
        parameters STRING, 
        explore_view STRING, 
        model_name STRING, 
        table_name STRING, 
        column_schema STRING, 
        desc_vector ARRAY<FLOAT64>)"""
        .format(project_id=self.project_id, dataset=self.dataset, table_name=self.table_name)
      )
    print(query.to_dataframe())
    errors = self.bigquery_client.query(
      """CREATE VECTOR INDEX IF NOT EXISTS `{table_name}_desc_vector_idx` ON `{project_id}.{dataset}.{table_name}`(desc_vector) OPTIONS(index_type='IVF', distance_type='COSINE')
      """.format(project_id=self.project_id, dataset=self.dataset, table_name=self.table_name)
    )
    print(errors)

  def insert_record(self, insertRecords: List[SqlSearchSchema]) -> None:
    records = [record.to_dict() for record in insertRecords]
    result = self.bigquery_client.insert_rows_json(self.table_ref, records)
    print(result)
  
  # Select a similar row from the table
  def select_similar_query(self, desc_vector):
    job_config = bigquery.QueryJobConfig(
      query_parameters=[
          bigquery.ArrayQueryParameter("desc_vector", "FLOAT64", desc_vector),
      ]
    )
    query = self.bigquery_client.query(
      """SELECT base.uuid, base.sql, base.description, base.parameters, base.explore_view, base.model_name, base.table_name, base.column_schema,  distance
      FROM VECTOR_SEARCH(TABLE `cc_default.tb_sql_search_target`, 'desc_vector', (select @desc_vector as desc_vector) , top_k => 5, options => '{"fraction_lists_to_search": 0.005}')  """
      #.format(project_id=self.project_id, dataset=self.dataset, table_name=self.table_name)
      ,job_config=job_config
    )
    return query.to_dataframe()
