"""
Script to deploy Flows.
"""
from prefect.deployments import Deployment
from prefect.infrastructure import DockerContainer
from prefect.orion.schemas.schedules import CronSchedule

from src.config import prefect_fs
from src.oryx_equipment_loss.flow import oryx_equipment_loss_flow


oryx_equipment_loss_deployment: Deployment = Deployment.build_from_flow(
    flow=oryx_equipment_loss_flow,
    name="Oryx Equipment Loss",
    infrastructure=DockerContainer.load("oryx-equipment-loss-environment"),
    schedule=CronSchedule(cron="0 1 * * *"),
    storage=prefect_fs
)
