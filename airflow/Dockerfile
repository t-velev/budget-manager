# Define "Base Image"
FROM apache/airflow:3.1.7

# Define the working directory of the app
WORKDIR /opt/airflow

USER airflow

COPY airflow/requirements.txt .

# Install needed libraries
RUN pip install "apache-airflow==3.1.7" --no-cache-dir \
                -r requirements.txt \
                --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.7/constraints-3.12.txt"

# Create isolated virtual environment
RUN python -m venv /opt/airflow/dbt_venv
RUN /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-postgres   

# --- STEP 1: COPY EVERYTHING FIRST ---
# Switch to root to ensure we can move files and change permissions
USER root
COPY --chown=airflow:root airflow/ .

# --- STEP 2: FIX PERMISSIONS ON THE COPIED FILES ---
# Now that the files are inside, we force ownership and create missing dirs
RUN mkdir -p /opt/airflow/dbt/budget_manager/logs /opt/airflow/dbt/budget_manager/target && \
    chown -R airflow:root /opt/airflow/dbt && \
    chmod -R 775 /opt/airflow/dbt/budget_manager/logs

# --- STEP 3: SWITCH BACK TO AIRFLOW ---
USER airflow