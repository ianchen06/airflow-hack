# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Example DAG demonstrating the usage of the PythonOperator."""

import time
from pprint import pprint
import logging

import airflow
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(1),
}

dag = DAG(
    dag_id='mysql2hive2',
    default_args=args,
    schedule_interval="0 * * * *",
)


# [START howto_operator_python]
def print_context(ds, **kwargs):
    """Print the Airflow context and ds variable from the context."""
    pprint(kwargs)
    print(ds)
    return 'Whatever you return gets printed in the logs'

def dag_run(context, dag_run_obj):
    print("[dag_run] %s"%dag_run_obj)
    return dag_run_obj

run_this = PythonOperator(
    task_id='print_the_context',
    provide_context=True,
    python_callable=print_context,
    dag=dag,
)

trigger_hdfs = BashOperator(
    task_id='trigger_hdfs',
    bash_command="""
    set -x

    if [["$(airflow trigger_dag -r trig__{{ execution_date }} -e {{ execution_date }} example_python_operator)" != 0]]; then
      airflow clear -c -s {{ execution_date }} -e {{ execution_date }} example_python_operator
    fi
    """,
    dag=dag,
)

run_this.set_downstream(trigger_hdfs)
