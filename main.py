"""

"""
import click


@click.group
def cli():
    ...


###################################################################################################
# Deployments
###################################################################################################

@cli.group
def deploy():
    ...


@deploy.command
def oryx_equipment_loss(upload: bool = True):
    from src.oryx_equipment_loss.deploy import oryx_equipment_loss_deployment
    oryx_equipment_loss_deployment.apply(upload=upload)


###################################################################################################
# Flows
###################################################################################################

@cli.group
def run():
    ...


@run.command
def oryx_equipment_loss():
    from src.oryx_equipment_loss.flow import oryx_equipment_loss_flow
    oryx_equipment_loss_flow()



if __name__ == '__main__':
    cli()
