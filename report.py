#!/usr/bin/env python3

import configparser
import requests
import json
import sys

config = configparser.ConfigParser()

# Define our global variables
API_TOKEN = 'TOKEN'
asana_base_URL = 'https://app.asana.com/api/1.0'
project_name = 'PROJECT'

def get_configuration(config_file):
    ''' Read the configuration file '''
    global API_TOKEN
    global asana_base_URL
    global project_name
    config.read(config_file)

    try:
        asana_base_URL = config['DEFAULT']['asana_base_URL']
        API_TOKEN = config['DEFAULT']['API_TOKEN']
        project_name = config['DEFAULT']['project_name']
    except KeyError:
        print("Unable to read configuration file %s"% (config_file))
        sys.exit(2)

def check_authentication():
    ''' Make a request for user information to see if we're authenticated '''
    global API_TOKEN
    global asana_base_URL
    uri = '%s/users/me'% (asana_base_URL,)
    headers = {'Authorization': 'Bearer %s'% (API_TOKEN)}

    r = requests.get(uri, headers=headers)
    r.raise_for_status()
    return r

def get_projects():
    ''' Get the list of projects '''
    global API_TOKEN
    global asana_base_URL
    uri = '%s/projects'% (asana_base_URL,)
    headers = {'Authorization': 'Bearer %s'% (API_TOKEN)}

    r = requests.get(uri, headers=headers)
    r.raise_for_status()
    data = json.loads(r.text)
    return data['data']

def get_sections(project_gid):
    ''' Get the list of sections for a given project '''
    global API_TOKEN
    global asana_base_URL
    uri = '%s/projects/%s/sections'% (asana_base_URL, project_gid)
    headers = {'Authorization': 'Bearer %s'% (API_TOKEN)}

    r = requests.get(uri, headers=headers)
    r.raise_for_status()
    data = json.loads(r.text)
    return data['data']

def get_tasks(section):
    ''' Get the list of tasks for a given section_gid '''
    global API_TOKEN
    global asana_base_URL
    #TODO: We're not paginating here, but we prolly should. i.e. limit=100
    uri = '%s/sections/%s/tasks?opt_fields=dependencies,custom_fields,name,num_subtasks'% (asana_base_URL, section['gid'])
    headers = {'Authorization': 'Bearer %s'% (API_TOKEN)}
    tasks = []

    r = requests.get(uri, headers=headers)
    r.raise_for_status()
    data = json.loads(r.text)
    # There's lots of metadata in the metadata. Filter it out
    for task in data['data']:
        t = {}
        t['gid'] = task['gid']
        t['section'] = section['name']
        t['name'] = "\"%s\""% (task['name'],)
        t['num_subtasks'] = task['num_subtasks']
        for cf in task['custom_fields']:
            if cf['type'] == "text":
                t[cf['name']] = "\"%s\""% (cf['text_value'],)
            elif cf['type'] == "number":
                t[cf['name']] = cf['number_value']
            elif cf['type'] == "enum":
                if cf['enum_value'] is not None:
                    t[cf['name']] = cf['enum_value']['name']
            elif cf['type'] == "multi_enum":
                t[cf['name']] = []
                for v in cf['multi_enum_values']:
                    t[cf['name']].append(v['name'])

        tasks.append(t)

    return tasks

def get_stories(task):
    ''' Get the list of stories for a given task_gid '''
    global API_TOKEN
    global asana_base_URL
    #TODO: We're not paginating here, but we prolly should. i.e. limit=100
    uri = '%s/tasks/%s/stories'% (asana_base_URL, task['gid'])
    headers = {'Authorization': 'Bearer %s'% (API_TOKEN)}
    stories = []
    
    r = requests.get(uri, headers=headers)
    r.raise_for_status()
    data = json.loads(r.text)
    for story in data['data']:
        print(story)

## MAIN

get_configuration('report.conf')
check_authentication()

# Get the list of projects
projects = get_projects()

# Get the project ID
project_gid = None
for project in projects:
    if project["name"] == project_name:
        project_gid = project["gid"]
        break

if project_gid is None:
    print("Couldn't find project with name %s"% (project_name,))
    sys.exit(2)

# Get the list of sections
sections = get_sections(project_gid)

tasks = []

for section in sections:
    tasks.extend(get_tasks(section))

# Get a list of fields
fields = ['gid', 'name', 'num_subtasks']
for t in tasks:
    for f in t.keys():
        if f not in fields:
            fields.append(f)

# Print the field header
field_list = ""
for f in fields:
    field_list += "%s,"% (f)
# Strip the last comma
print(field_list[:-1])

# # Print comments
# for t in tasks:
#     get_stories(t)    

# Print the csv
for t in tasks:
    task_string = ""
    for f in fields:
        try:
            v = ""
            # Handle lists and nones
            if type(t[f]) == list:
                for i in t[f]:
                    v += "%s|"% (i,)
                v = v[:-1]
            elif t[f] == "\"None\"":
                v = ""
            elif t[f] is None:
                v = ""
            else:
                v = t[f]
            task_string += "%s,"% (v,)
        except KeyError:
            task_string += ","
    # Strip the last comma
    print(task_string[:-1])

