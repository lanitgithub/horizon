import os
import re
import gitlab
import tempfile

url = 'https://gitlab.dks.lanit.ru/load_testing/egrip_egrul/-/blob/master/scripts/dynamic_egrip_egrul.jmx'

regex = r'^(?P<main_url>https+:\/\/.+?)\/(?P<group_name>.+?)\/(?P<project_name>.+?)\/-\/blob\/' \
        r'(?P<branch_name>.+?)\/(?P<path>.+\.jmx)$'

match = re.match(regex, url)

if not match:
        pass  # TODO raise exception

url_components = match.groupdict()
print(url_components)

gl = gitlab.Gitlab(url_components['main_url'], private_token='E_caWLyJbu_CerxoWNiE')

# get project name by id
project_id = gl.search('projects', url_components['project_name'])[0]['id']


project = gl.projects.get(project_id)

temp_dir = tempfile.TemporaryDirectory(prefix='jmeter_sources_')
print(temp_dir.name)

base_script_filename = os.path.basename(url_components['path'])

with open(os.path.join(temp_dir.name, base_script_filename), 'wb') as f:
        project.files.raw(file_path=url_components['path'], ref=url_components['branch_name'], action=f.write)

# call this after test stopped
temp_dir.cleanup()
