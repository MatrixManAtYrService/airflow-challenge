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
from typing import Optional

from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.hooks.base_aws import AwsBaseHook
from airflow.providers.amazon.aws.operators.sagemaker_base import SageMakerBaseOperator


class SageMakerProcessingOperator(SageMakerBaseOperator):
    """
    Initiate a SageMaker processing job.

    This operator returns The ARN of the processing job created in Amazon SageMaker.

    :param config: The configuration necessary to start a processing job (templated).

        For details of the configuration parameter see :py:meth:`SageMaker.Client.create_processing_job`
    :type config: dict
    :param aws_conn_id: The AWS connection ID to use.
    :type aws_conn_id: str
    :param wait_for_completion: If wait is set to True, the time interval, in seconds,
        that the operation waits to check the status of the processing job.
    :type wait_for_completion: bool
    :param print_log: if the operator should print the cloudwatch log during processing
    :type print_log: bool
    :param check_interval: if wait is set to be true, this is the time interval
        in seconds which the operator will check the status of the processing job
    :type check_interval: int
    :param max_ingestion_time: If wait is set to True, the operation fails if the processing job
        doesn't finish within max_ingestion_time seconds. If you set this parameter to None,
        the operation does not timeout.
    :type max_ingestion_time: int
    :param action_if_job_exists: Behaviour if the job name already exists. Possible options are "increment"
        (default) and "fail".
    :type action_if_job_exists: str
    """

    def __init__(
        self,
        *,
        config: dict,
        aws_conn_id: str,
        wait_for_completion: bool = True,
        print_log: bool = True,
        check_interval: int = 30,
        max_ingestion_time: Optional[int] = None,
        action_if_job_exists: str = "increment",  # TODO use typing.Literal for this in Python 3.8
        **kwargs,
    ):
        super().__init__(config=config, aws_conn_id=aws_conn_id, **kwargs)

        if action_if_job_exists not in ("increment", "fail"):
            raise AirflowException(
                "Argument action_if_job_exists accepts only 'increment' and 'fail'. "
                f"Provided value: '{action_if_job_exists}'."
            )
        self.action_if_job_exists = action_if_job_exists
        self.wait_for_completion = wait_for_completion
        self.print_log = print_log
        self.check_interval = check_interval
        self.max_ingestion_time = max_ingestion_time
        self._create_integer_fields()

    def _create_integer_fields(self) -> None:
        """Set fields which should be casted to integers."""
        self.integer_fields = [
            ['ProcessingResources', 'ClusterConfig', 'InstanceCount'],
            ['ProcessingResources', 'ClusterConfig', 'VolumeSizeInGB'],
        ]
        if 'StoppingCondition' in self.config:
            self.integer_fields += [['StoppingCondition', 'MaxRuntimeInSeconds']]

    def expand_role(self) -> None:
        if 'RoleArn' in self.config:
            hook = AwsBaseHook(self.aws_conn_id, client_type='iam')
            self.config['RoleArn'] = hook.expand_role(self.config['RoleArn'])

    def execute(self, context) -> dict:
        self.preprocess_config()

        processing_job_name = self.config["ProcessingJobName"]

        if self.hook.find_processing_job_by_name(processing_job_name):
            raise AirflowException(
                f"A SageMaker processing job with name {processing_job_name} already exists."
            )

        self.log.info("Creating SageMaker processing job %s.", self.config["ProcessingJobName"])
        response = self.hook.create_processing_job(
            self.config,
            wait_for_completion=self.wait_for_completion,
            check_interval=self.check_interval,
            max_ingestion_time=self.max_ingestion_time,
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise AirflowException(f'Sagemaker Processing Job creation failed: {response}')
        return {'Processing': self.hook.describe_processing_job(self.config['ProcessingJobName'])}
