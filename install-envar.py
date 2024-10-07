#!/usr/bin/env python

import os, argparse
from src import tools

parser = argparse.ArgumentParser(
    description="Get a helm chart's default values when using helm dependencies. \n\n Usage: helm get-values "
                "<chartname>",
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', type=str, help='the name of the Chart.yaml you want to render')
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-v', type=str, help='the name of the charts\' values you want to render', required=True)
requiredNamed.add_argument('--name', type=str, help='the name of the local helm chart', required=True)
args = vars(parser.parse_args())

tempdir = "./.temp"


# Fetch helm chart to temp dir
def execute(values_dir, chart_dir, name):
    if not values_dir and not chart_dir:
        print("Nothing to do, please pass value.yaml as required and Chart.yaml as optional")
        exit()
    temp_dir_without_file, filetemplate = tools.split_dir_from_template(tempdir + values_dir)
    temp_dir_without_file = temp_dir_without_file + "/" + name
    tools.setup(temp_dir_without_file)
    tools.copy_and_overwrite(tools.split_dir_from_template(values_dir)[0] + "/templates",
                                   temp_dir_without_file + "/templates")
    tools.render(values_dir, temp_dir_without_file)
    if chart_dir:
        tools.render(chart_dir, temp_dir_without_file)
    # Execute the command
    tools.download_dependencies(temp_dir_without_file)
    tools.verify_chart(temp_dir_without_file)
    tools.execute_helm(filetemplate, name, temp_dir_without_file)
    # Clean up
    tools.delete_folder(tempdir)


if __name__ == '__main__':
    execute(args['v'], args['c'], args['name'])
