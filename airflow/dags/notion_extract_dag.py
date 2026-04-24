from airflow.sdk import dag, task, Param
from sqlalchemy import create_engine, text
import pendulum
import os

postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

log_schema_name = 'warehouse'
log_table_name = 'sys_etl_dag_task_log'
engine = create_engine(f'postgresql://{db_user}:{db_pass}@budget-db:5432/{postgres_db}')

default_args = {
    # 'retries': 1,
    # 'retry_delay': pendulum.duration(seconds=10),
    'trigger_rule': 'none_failed'
}

@dag(
    dag_id = 'extract_notion_db',
    description = 'Extract data from Notion databases',
    start_date = pendulum.datetime(2026,3,9, tz='Europe/Sofia'),
    schedule = None,
    catchup = False,
    default_args = default_args,
    params={
        'Force tasks to run': Param(False, type="boolean"),
        'Select tasks to run': Param(['extract_db_account', 'extract_db_category', 'extract_db_subcategory', 'extract_db_year', 
                                      'extract_db_month'  , 'extract_db_budget'  , 'extract_db_transaction', 'dbt_build'], type="array",
                                       #########
                                       examples=['extract_db_account', 'extract_db_category', 'extract_db_subcategory', 'extract_db_year', 
                                                 'extract_db_month'  , 'extract_db_budget'  , 'extract_db_transaction', 'dbt_build'])
    }    
)
def extract_notion_db():

    def has_to_start(context):

        # Extract task name/id from context
        ti = context.get('task_instance')
        task_name = ti.task_id

        # Extract params from context
        params = context.get('params', {})
        force_tasks = params.get('Force tasks to run', False)
        tasks_to_run = params.get('Select tasks to run', [])

        # Calc time since last successful run
        prev_run_time = context.get('prev_start_date_success')
        current_time = pendulum.now()
        time_since_last_run = current_time - prev_run_time

        # Don't run the task if last successful run was less than 15 mins ago or it isn't manually forced
        if time_since_last_run < pendulum.duration(minutes=15) and force_tasks == False:
            print(f'Last successful run was before: {time_since_last_run.in_words()}')
            print(f'Skipping {task_name}...')
            return False

        # The task has to be selected to run, no matter if it's forced or not
        elif task_name not in tasks_to_run:
            print(f'Skipping {task_name} because it isn\'t selected.')
            return False            

        # Run the task if it is selected and enough time has passed
        else:
            print(f'Running {task_name}...')
            return True


    def write_to_db_log(context):

        ti = context['task_instance']
        dr = context['dag_run']

        # Convert the dag's run date to local tz and format it
        run_id = pendulum.instance(dr.logical_date).in_tz('Europe/Sofia').format('YYYYMMDDHHmmss')

        # Calc time delta and convert it to minutes with 2 decimal places (1.5 for 90 seconds)
        duration_delta = ti.end_date - ti.start_date
        duration_minutes = round(duration_delta.total_seconds() / 60, 2)

        values = {
            'run_id'     : run_id,
            'run_type'   : dr.run_type,
            'dag_name'   : ti.dag_id,
            'task_name'  : ti.task_id,
            'start_time' : ti.start_date,
            'end_time'   : ti.end_date,
            'duration'   : duration_minutes,
            'status'     : ti.state,
            'error_msg'  : str(context.get('exception')) if context.get('exception') else None
        }

        with engine.begin() as conn:
            query = text(f"""
                          INSERT into {log_schema_name}.{log_table_name}
                          VALUES (:run_id, :run_type, :dag_name, :task_name, :start_time, :end_time, :duration, :status, :error_msg)
                          """)
            conn.execute(query, values)

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_account():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_account.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_budget():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_budget.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_category():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_category.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_transaction():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_transaction.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_month():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_month.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_subcategory():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_subcategory.py
               """        

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def extract_db_year():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_ntn_year.py
               """

    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log, 
               on_failure_callback=write_to_db_log)
    def dbt_build():
        return "/opt/airflow/dbt_venv/bin/dbt build " \
               "--project-dir /opt/airflow/dbt/budget_manager " \
               "--profiles-dir /opt/airflow/dbt/budget_manager " \
               "--exclude resource_type:seed " \
               "--vars '{\"run_id\": \"{{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }}\"}'"

    extract_db_account() >> extract_db_category() >> extract_db_subcategory() \
    >> extract_db_year() >> extract_db_month() >> extract_db_budget() >> extract_db_transaction() \
    >> dbt_build()

extract_notion_db()