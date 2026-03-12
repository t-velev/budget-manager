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

# Copy scripts to working dir
COPY --chown=airflow:0 airflow/ .