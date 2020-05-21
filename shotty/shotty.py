import boto3
import botocore
import click
import sys

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

@click.group('cli')
@click.option('--profile', default='shotty',
              help="Specify profile for commands")
def cli(profile):
    """Shotty manages snapshots"""
    try:
        print("Using profile {0}".format(profile))
        session = boto3.Session(profile_name=profile)
        ec2 = session.resource('ec2')
    except botocore.exceptions.ProfileNotFound as e:
        print(str(e))
        sys.exit(1)
    except:
        print(str(sys.exc_info()[0]))
        raise





@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project',
              default=None,
              help="Only snapshots for project (tag project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
              help="List all snapshots for each volume, not just most recent")
def list_snapshots(project, list_all):
    "List EC2 snapshots"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all: break
    return






@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project',
              default=None,
              help="Only volumes for project (tag project:<name>)")
def list_volumes(project):
    "List EC2 volumes"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return








@cli.group('instances')
def instances():
    """Commands for instances"""

def filter_instances(project):
    instances = []

    if project:
        filters=[{
            'Name': 'tag:project',
            'Values': [project],
        }]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0] == 'pending'

def verify_project(project, force):
    "Check that project is set or force is used"
    if not project and not force:
        print("no project, stopping command - use --force to override")
        return False
    return True

@instances.command('snapshot',
                  help="Create snapshot of all volumes")
@click.option('--project',
              default=None,
              help="Only instances for project (tag project:<name>)")
@click.option('--force', 'force', default=False, is_flag=True,
              help="Allow command without specifying a project.")
def create_snapshots(project, force):
    "Create snapshots for a project's EC2 instances"
    instances = filter_instances(project)

    if not verify_project(project, force):
        return

    for i in instances:
        print("Stopping {0}...".format(i.id))
        i.stop()

        i.wait_until_stopped()
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("\tSkipping {0}, snapshot already in progress.".format(v.id))
            print("Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by SnapshotAlyzer-30000")

        print("Starting {0}...".format(i.id))
        i.start()
        i.wait_until_running()

    print("Job's done")
    return

@instances.command('list')
@click.option('--project',
              default=None,
              help="Only instances for project (tag project:<name>)")
def list_instances(project):
    "List EC2 instances"
    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('project', '<no project>')
        )))

    return

@instances.command('stop')
@click.option('--project',
              default=None,
              help="Only instances for project (tag project:<name>)")
@click.option('--force', 'force', default=False, is_flag=True,
              help="Allow command without specifying a project.")
def stop_instances(project, force):
    "Stop EC2 instances"

    if not verify_project(project, force):
        return
    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("\tCould not stop {0} ".format(i.id + str(e)))
            continue
    return

@instances.command('start')
@click.option('--project',
              default=None,
              help="Only instances for project (tag project:<name>)")
@click.option('--force', 'force', default=False, is_flag=True,
              help="Allow command without specifying a project.")
def start_instances(project, force):
    "Start EC2 instances"

    if not verify_project(project, force):
        return
    instances = filter_instances(project)

    for i in instances:
        print("Starting {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("\tCould not start {0} ".format(i.id + str(e)))
            continue

    return

@instances.command('reboot')
@click.option('--project',
              default=None,
              help="Only instances for project (tag project:<name>)")
def reboot_instances(project):
    "Reboot those dang EC2 instances"
    instances = filter_instances(project)

    for i in instances:
        print("Rebooting {0}".format(i.id))
        try:
            i.reboot()
        except botocore.exceptions.ClientError as e:
            print("\tUnable to reboot {0} ".format(i.id + str(e)))





if __name__ == '__main__':
    cli()
