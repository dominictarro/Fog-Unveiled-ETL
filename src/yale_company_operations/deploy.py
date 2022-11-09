"""
Script to deploy Flows.
"""
from prefect.deployments import Deployment
from prefect.infrastructure import DockerContainer
from prefect.orion.schemas.schedules import CronSchedule

from src.config import prefect_fs
from src.yale_company_operations.flow import yale_company_operations_flow


yale_company_operations_deployment: Deployment = Deployment.build_from_flow(
    flow=yale_company_operations_flow,
    name="Yale Company Operations",
    infrastructure=DockerContainer.load("yale-company-operations-environment"),
    schedule=CronSchedule(cron="0 1 * * *"),
    storage=prefect_fs
)
