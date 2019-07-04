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
from airflow.operators.dagrun_operator import TriggerDagRunOperator

import json
from airflow.utils import timezone
from airflow import settings
from airflow.models import DagBag
from airflow.operators.dagrun_operator import DagRunOrder
from airflow.utils.state import State

args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(1),
}

dag = DAG(
    dag_id='mysql2hive',
    default_args=args,
    schedule_interval="0 * * * *",
)

class TriggerDagRunOperator2(TriggerDagRunOperator):
    def __init__(
            self,
            trigger_dag_id,
            python_callable=None,
            execution_date=None,
            *args, **kwargs):
        super(TriggerDagRunOperator2, self).__init__(execution_date=execution_date,
                                                     python_callable=python_callable,
                                                     trigger_dag_id=trigger_dag_id,
                                                     *args, **kwargs)

    def execute(self, context):
        if self.execution_date is not None:
            run_id = 'trig__{}'.format(self.execution_date)
            self.execution_date = timezone.parse(self.execution_date)
        else:
            run_id = 'trig__' + timezone.utcnow().isoformat()
        dro = DagRunOrder(run_id=run_id)
        if self.python_callable is not None:
            dro = self.python_callable(context, dro)
        if dro:
            dbag = DagBag(settings.DAGS_FOLDER)
            trigger_dag = dbag.get_dag(self.trigger_dag_id)

            if not trigger_dag.get_dagrun(execution_date=self.execution_date):
                dr = trigger_dag.create_dagrun(
                            run_id=dro.run_id,
                            state=State.RUNNING,
                            conf=json.dumps(dro.payload),
                            execution_date=self.execution_date,
                            external_trigger=True
                )
                logging.info("Creating DagRun %s"%dr)
            else:
                trigger_dag.clear(
                   start_date = self.execution_date,
                   end_date = self.execution_date,
                   only_failed = False,
                   only_running = False,
                   confirm_prompt = False, 
                   reset_dag_runs = True, 
                   include_subdags= False,
                   dry_run = False 
                )
                logging.info("Cleared DagRun %s"%trigger_dag)
        else:
            self.log.info("Criteria not met, moving on")


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

trigger_hdfs = TriggerDagRunOperator2(
    task_id="trigger_the_dag",
    trigger_dag_id="example_python_operator",
    python_callable=dag_run,
    execution_date="{{ execution_date }}",
    dag=dag,
)

run_this.set_downstream(trigger_hdfs)
