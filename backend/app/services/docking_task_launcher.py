import os
from typing import Any, Dict, List

import boto3


REQUIRED_ENV_VARS = [
    "AWS_REGION",
    "AMRDRUGX_SCREENING_BUCKET",
    "DOCKING_ECS_CLUSTER_NAME",
    "DOCKING_ECS_TASK_DEFINITION",
    "DOCKING_ECS_CONTAINER_NAME",
    "ECS_SUBNET_IDS",
    "ECS_SECURITY_GROUP_ID",
]


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def _get_subnet_ids() -> List[str]:
    raw_subnet_ids = _get_required_env("ECS_SUBNET_IDS")

    subnet_ids = [
        subnet_id.strip()
        for subnet_id in raw_subnet_ids.split(",")
        if subnet_id.strip()
    ]

    if not subnet_ids:
        raise ValueError("ECS_SUBNET_IDS must contain at least one subnet ID.")

    return subnet_ids


def start_docking_fargate_task(
    job_id: str,
    input_key: str,
    output_key: str,
) -> Dict[str, Any]:
    for env_var in REQUIRED_ENV_VARS:
        _get_required_env(env_var)

    aws_region = _get_required_env("AWS_REGION")
    bucket_name = _get_required_env("AMRDRUGX_SCREENING_BUCKET")
    cluster_name = _get_required_env("DOCKING_ECS_CLUSTER_NAME")
    task_definition = _get_required_env("DOCKING_ECS_TASK_DEFINITION")
    container_name = _get_required_env("DOCKING_ECS_CONTAINER_NAME")
    security_group_id = _get_required_env("ECS_SECURITY_GROUP_ID")
    subnet_ids = _get_subnet_ids()

    ecs_client = boto3.client("ecs", region_name=aws_region)

    response = ecs_client.run_task(
        cluster=cluster_name,
        taskDefinition=task_definition,
        launchType="FARGATE",
        count=1,
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnet_ids,
                "securityGroups": [security_group_id],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": container_name,
                    "environment": [
                        {"name": "AWS_REGION", "value": aws_region},
                        {
                            "name": "AMRDRUGX_SCREENING_BUCKET",
                            "value": bucket_name,
                        },
                        {"name": "JOB_ID", "value": job_id},
                        {"name": "INPUT_KEY", "value": input_key},
                        {"name": "OUTPUT_KEY", "value": output_key},
                    ],
                }
            ]
        },
    )

    failures = response.get("failures", [])
    if failures:
        raise RuntimeError(f"ECS failed to start docking task: {failures}")

    tasks = response.get("tasks", [])
    if not tasks:
        raise RuntimeError("ECS did not return a started docking task.")

    task = tasks[0]

    return {
        "task_arn": task.get("taskArn"),
        "cluster_arn": task.get("clusterArn"),
        "last_status": task.get("lastStatus"),
        "desired_status": task.get("desiredStatus"),
        "launch_type": task.get("launchType"),
        "raw_failures": failures,
    }