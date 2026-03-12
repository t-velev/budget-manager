from airflow.sdk import dag, task
from datetime import datetime, timedelta

@dag(
    dag_id = 'extract_notion_db',
    description = 'Extract data from Notion databases',
    start_date = datetime(2026,3,9),
    schedule = None,
    catchup = False
)
def extract_notion_db():

    @task.bash
    def extract_db_accounts():
        return 'python /opt/airflow/src/extract_ntn_accounts.py'

    @task.bash
    def extract_db_budgets():
        return 'python /opt/airflow/src/extract_ntn_budgets.py'      
    
    @task.bash
    def extract_db_categories():
        return 'python /opt/airflow/src/extract_ntn_categories.py'   

    @task.bash
    def extract_db_inc_exp():
        return 'python /opt/airflow/src/extract_ntn_inc_exp.py'   

    @task.bash
    def extract_db_months():
        return 'python /opt/airflow/src/extract_ntn_months.py'   

    @task.bash
    def extract_db_subcategories():
        return 'python /opt/airflow/src/extract_ntn_subcategories.py'   

    @task.bash
    def extract_db_years():
        return 'python /opt/airflow/src/extract_ntn_years.py'                             

    extract_db_accounts()
    extract_db_budgets()
    extract_db_categories()
    extract_db_inc_exp()
    extract_db_months()
    extract_db_subcategories()
    extract_db_years()

extract_notion_db()