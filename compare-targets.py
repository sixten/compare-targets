#!/usr/bin/python3
# coding: utf8

from TargetInfo import TargetInfo
import click
import json
import os.path
import subprocess
import tempfile
from pbxproj import XcodeProject


@click.command()
@click.argument('project_file', type=click.Path(exists=True))
@click.argument('base_target')
@click.argument('app_target')
@click.option('--tool', '-t', default='bcompare', help='The tool to use for diffing the target info.')
def compare(project_file, base_target, app_target, tool):
  """Compares the configuration of APP_TARGET to BASE_TARGET in the project PROJECT_FILE."""
  
  # load project file
  if os.path.isdir(project_file):
    pbxfile = os.path.join(project_file, 'project.pbxproj')
    if os.path.isfile(pbxfile):
      project_file = pbxfile
    else:
      click.secho(f"! The specified directory doesn't seem to contain an Xcode project.", fg='red', bold=True)
      exit(1)
  try:
    project = XcodeProject.load(project_file)
  except:
    click.secho(f"! The specified file doesn't seem to be an Xcode project.", fg='red', bold=True)
    exit(1)
  
  # check for existence of both targets
  objs = project.objects.get_targets(base_target)
  if 1 != len(objs):
    click.secho(f"! Base target {base_target} not found in project.", fg='red', bold=True)
    exit(1)
  target1 = objs[0]
  
  objs = project.objects.get_targets(app_target)
  if 1 != len(objs):
    click.secho(f"! App target {app_target} not found in project.", fg='red', bold=True)
    exit(1)
  target2 = objs[0]
  
  # extract target details
  base_info = TargetInfo(project, target1)
  app_info = TargetInfo(project, target2)
  
  # invoke comparison
  use_tool = 0 == subprocess.call(['which', tool])
  
  with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as base_file:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as app_file:
      json.dump(base_info.dict(), base_file, indent=2, sort_keys=True)
      json.dump(app_info.dict(), app_file, indent=2, sort_keys=True)
      
      command = [tool if use_tool else 'opendiff', base_file.name, app_file.name]
      subprocess.run(command, capture_output=True)


if __name__ == '__main__':
    compare()
