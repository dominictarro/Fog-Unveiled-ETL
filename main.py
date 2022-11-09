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


@deploy.command
def yale_company_operations(upload: bool = True):
    from src.yale_company_operations.deploy import yale_company_operations_deployment
    yale_company_operations_deployment.apply(upload=upload)

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


@run.command
def yale_company_operations():
    from src.yale_company_operations.flow import yale_company_operations_flow
    yale_company_operations_flow()


if __name__ == '__main__':
    cli()
