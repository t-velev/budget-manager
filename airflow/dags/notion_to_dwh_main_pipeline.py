from airflow.sdk import dag, task, Param
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pendulum
import os

###################################################
## 1. Set initial vars
###################################################
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

log_schema_name = 'warehouse'
log_table_name = 'sys_etl_dag_task_log'
engine = create_engine(f'postgresql://{db_user}:{db_pass}@budget-db:5432/{postgres_db}')

default_args = {
    'retries': 1,
    'retry_delay': pendulum.duration(seconds=30),
    'trigger_rule': 'none_failed'
}

###################################################
## 2. Setup DAG
###################################################
@dag(
    dag_id = 'notion_to_dwh_main_pipeline',
    description = 'Extracts data from Notion databases and loads it to PostgreSQL.',
    start_date = pendulum.datetime(2026,4,24, tz='Europe/Sofia'),
    schedule = None,
    catchup = False,
    default_args = default_args,
    params={
        # Switch to force the tasks to run, even when time_since_last_run < 15 minutes
        'Force tasks to run': Param(False, type="boolean"),
        # Dropdown to manually select which tasks to run
        'Select tasks to run': Param(['extract_and_load_account', 'extract_and_load_category', 'extract_and_load_subcategory', 'extract_and_load_year',
                                      'extract_and_load_month'  , 'extract_and_load_budget'  , 'extract_and_load_transaction', 'execute_dbt_pipeline'], type="array",
                                       #########
                                       examples=['extract_and_load_account', 'extract_and_load_category', 'extract_and_load_subcategory', 'extract_and_load_year',
                                                 'extract_and_load_month'  , 'extract_and_load_budget'  , 'extract_and_load_transaction', 'execute_dbt_pipeline'])
    }
)

###################################################
## 3. Define the pipeline
###################################################
def notion_to_dwh_main_pipeline():

    def has_to_start(context) -> bool:
        """
        Check if a task should run.
        Tasks should have 15 mins window between them. If the time since last successful run is less,
        the task can run only if 1) is forced through force_tasks=True and 2) is selected in tasks_to_run.

        Params: context (internal to Airflow, not provided by me)

        Returns: True (task will run) or False (task won't run)
        """

        # Extract task name/id from context
        ti = context.get('task_instance')
        task_name = ti.task_id

        # Extract params from context
        params = context.get('params', {})
        force_tasks = params.get('Force tasks to run', False)
        tasks_to_run = params.get('Select tasks to run', [])

        # Get the last successful task run date and time from warehouse.sys_etl_dag_task_log
        try:
            with engine.begin() as conn:
                query = text(f"select max(end_time) from {log_schema_name}.{log_table_name} where task_name = '{task_name}' and status = 'success'")
                prev_task_success_time = conn.execute(query).fetchone()[0]  # first element of row object

            if prev_task_success_time:
                prev_task_success_time = pendulum.instance(prev_task_success_time).set(tz='Europe/Sofia')
            else:
                prev_task_success_time = pendulum.datetime(1990, 1, 1, tz='Europe/Sofia')  # If the dag is executed for the first time

        except SQLAlchemyError as e:
            print(f'Error: Could not fetch the max(end_time) for {log_schema_name}.{log_table_name} . Details: {e}')
            raise

        # Calc time since last successful run
        current_time = pendulum.now('Europe/Sofia')
        time_since_last_run = current_time - prev_task_success_time

        # Don't run the task if last successful run was less than 15 mins ago or it isn't manually forced
        if time_since_last_run < pendulum.duration(minutes=15) and force_tasks == False:
            print(f'Last successful task run was before: {time_since_last_run.in_words()}')
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


    def write_to_db_log(context) -> None:
        """
        Write dag and tasks runtime statistics to warehouse.sys_etl_dag_task_log table in Postgres.

        Returns:
            None
        """

        # Set Airflow context vars
        ti = context['task_instance']
        dr = context['dag_run']

        # Convert the dag's run date to local tz and format it
        run_id = pendulum.instance(dr.logical_date).in_tz('Europe/Sofia').format('YYYYMMDDHHmmss')

        # Calc time delta and convert it to minutes with 2 decimal places (1.5 for 90 seconds)
        duration_delta = ti.end_date - ti.start_date
        duration_minutes = round(duration_delta.total_seconds() / 60, 2)

        # Insert into log data into warehouse.sys_etl_dag_task_log
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

        try:
            with engine.begin() as conn:
                query = text(f"""
                              INSERT into {log_schema_name}.{log_table_name}
                              VALUES (:run_id, :run_type, :dag_name, :task_name, :start_time, :end_time, :duration, :status, :error_msg)
                              """)
                conn.execute(query, values)

        # Not raising error, because task is successful. Just print info.
        except SQLAlchemyError as e:
            print(f'Warning: Task {values["task_name"]} succeeded, but could not write to sys_etl_dag_task_log. Details: {e}')


    ###################################################
    ## Task EXTRACT_AND_LOAD_ACCOUNT
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_account():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_account.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_BUDGET
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_budget():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_budget.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_CATEGORY
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_category():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_category.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_TRANSACTION
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_transaction():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_transaction.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_MONTH
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_month():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_month.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_SUBCATEGORY
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_subcategory():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_subcategory.py
               """

    ###################################################
    ## Task EXTRACT_AND_LOAD_YEAR
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def extract_and_load_year():
        # Inject the run_id directly into the bash execution environment
        return """
               run_id={{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }} \
               dag_name={{ dag.dag_id }} \
               task_name={{ task.task_id }} \
               python /opt/airflow/src/extract_and_load_year.py
               """

    ###################################################
    ## Task EXECUTE_DBT_PIPELINE
    ###################################################
    @task.run_if(has_to_start)
    @task.bash(on_success_callback=write_to_db_log,
               on_failure_callback=write_to_db_log)
    def execute_dbt_pipeline():
        return "/opt/airflow/dbt_venv/bin/dbt build " \
               "--project-dir /opt/airflow/dbt/budget_manager " \
               "--profiles-dir /opt/airflow/dbt/budget_manager " \
               "--exclude resource_type:seed " \
               "--vars '{\"run_id\": \"{{ logical_date.in_timezone('Europe/Sofia').format('YYYYMMDDHHmmss') }}\"}'"

    ###################################################
    ## Define task dependencies
    ###################################################
    extract_and_load_account() >> extract_and_load_category() >> extract_and_load_subcategory() \
    >> extract_and_load_year() >> extract_and_load_month() >> extract_and_load_budget() >> extract_and_load_transaction() \
    >> execute_dbt_pipeline()

###################################################
## 4. Call/execute the pipeline
###################################################
notion_to_dwh_main_pipeline()