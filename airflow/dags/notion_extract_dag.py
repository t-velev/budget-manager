from airflow.sdk import dag, task
from datetime import datetime, timedelta

default_args = {
    'retries': 1,
    'retry_delay': timedelta(seconds=10)
}

@dag(
    dag_id = 'extract_notion_db',
    description = 'Extract data from Notion databases',
    start_date = datetime(2026,3,9),
    schedule = None,
    catchup = False,
    default_args = default_args
)
def extract_notion_db():

    @task.bash
    def extract_db_account():
        return 'python /opt/airflow/src/extract_ntn_account.py'

    @task.bash
    def extract_db_budget():
        return 'python /opt/airflow/src/extract_ntn_budget.py'      
    
    @task.bash
    def extract_db_category():
        return 'python /opt/airflow/src/extract_ntn_category.py'   

    @task.bash
    def extract_db_transaction():
        return 'python /opt/airflow/src/extract_ntn_transaction.py'   

    @task.bash
    def extract_db_month():
        return 'python /opt/airflow/src/extract_ntn_month.py'   

    @task.bash
    def extract_db_subcategory():
        return 'python /opt/airflow/src/extract_ntn_subcategory.py'   

    @task.bash
    def extract_db_year():
        return 'python /opt/airflow/src/extract_ntn_year.py'    
    
    @task.bash
    def dbt_build():
        return "/opt/airflow/dbt_venv/bin/dbt build " \
               "--project-dir /opt/airflow/dbt/budget_manager " \
               "--profiles-dir /opt/airflow/dbt/budget_manager " \
               "--exclude resource_type:seed "

    extract_db_account() >> extract_db_category() >> extract_db_subcategory() \
    >> extract_db_year() >> extract_db_month() >> extract_db_budget() >> extract_db_transaction() \
    >> dbt_build()

extract_notion_db()