import glob
import json
import os
import textwrap
import re

valid_types = {'datetime': True, 'string': True, 'int': True, 'boolean': True, 'long': True, 'bool': True, 'dynamic': True, 'real': True, 'guid': True, 'double': True}

# Extract tables from markdown files in Microsoft documentation.
def get_table_details(fn, base_dir):
    inside_table = False
    table_name = None
    details = {}
    data = open(fn).read()
    # Parse [!INCLUDE [awscloudtrail](../includes/awscloudtrail-include.md)]
    for include_fn in re.findall(r'\[!INCLUDE \[.*?\]\((.*?)\)\]', data):
        if 'reusable-content' in include_fn:
            print(include_fn)
            exit()
        include_path = os.path.abspath(os.path.join(os.path.dirname(fn), include_fn))
        parsed_dir = os.path.dirname(os.path.dirname(include_path)) + os.sep
        if not parsed_dir.startswith(base_dir + os.sep):
            raise Exception(f"Include path {parsed_dir} is not in {base_dir}")
        data += open(include_path).read() + '\n'

    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.replace('`','')
        if not table_name and line.startswith('# '):
            table_name = line.split()[1]
        if (
            line.lower().startswith('## columns')
            or line.lower().startswith('| column name')
            or line.lower().startswith('|column name')
            ):
            inside_table = True
            continue
        # if not line.startswith('|'):
        #     inside_table = False
        if line.startswith('#'):
            inside_table = False
        if not inside_table or not line.startswith('|'):
            continue
        column_details = line.replace(' ','').replace('\t','').split('|')
        if len(column_details) < 4:
            continue
        column_name = column_details[1]
        column_type = column_details[2].lower()
        if column_type == 'integer':
            column_type = 'int'
        if column_type == 'bigint':
            column_type = 'long'
        if column_type == 'list':
            column_type = 'string' # some tables refer to non-existing type 'list'
        if column_type == 'enum':
            column_type = 'string' # some tables refer to non-existing type 'enum'
        if column_type == 'nullablebool':
            column_type = 'bool' # some tables refer to non-existing type 'nullablebool'
        if column_type == 'boolean':
            column_type = 'bool' # The bool and boolean data types are equivalent.
        if not column_type:
            continue
        if column_name == 'Column' or column_name.startswith('--') or not column_name:
            continue
        if not column_type in valid_types:
            raise Exception(f"{column_type} is not a valid column type - table: {table_name} column_name: {column_name} column: {column_details}")
        details[column_name] = column_type
    return table_name, details

def merge_additional_columns(tables, env_name):
    additional_columns = json.load(open('additional_columns.json'))[env_name]
    for table_name, extra_fields in additional_columns.items():
        if table_name not in tables:
            tables[table_name] = {}
        for field_name, field_type in extra_fields.items():
            tables[table_name][field_name] = field_type

environments = {
    'm365': {
         'dir_name': 'defender-docs/defender-xdr',
         'base_dir': 'defender-docs',
         'glob': '*-table.md',
         'help': textwrap.dedent("""
            git clone --filter=blob:none --sparse --depth=1 https://github.com/MicrosoftDocs/defender-docs ; cd defender-docs ; git sparse-checkout set defender-docs/defender-xdr ; cd ..
        """),
        'magic_functions': [
            'AssignedIPAddresses',
            'FileProfile',
            'DeviceFromIP',
            'SeenBy'
        ]
    },
    'sentinel': {
       'dir_name': 'azure-reference-other/azure-monitor-ref/tables',
       'base_dir': 'azure-reference-other',
         'glob': '*.md',
       'help': textwrap.dedent("""
            git clone --depth=1 https://github.com/MicrosoftDocs/azure-reference-other ; cd azure-reference-other ; git checkout bea53845fef94ad4f1887d306e6618a34efefc01 ; cd ..
        """),
    }
}

def main():
    environment_details = {}
    for env_name, env_details in environments.items():
        if not os.path.exists(env_details['dir_name']):
            print(f"ERROR: {env_details['dir_name']} does not exist. To create it, run:\n{env_details['help'].strip()}")
            exit(1)
        base_dir = os.path.abspath(env_details['base_dir'])
        tables = {}
        glob_pattern = os.path.join(env_details['dir_name'], env_details['glob'])
        for table_fn in sorted(glob.glob(glob_pattern)):
            table_name, details = get_table_details(table_fn, base_dir)
            tables[table_name] = details
        merge_additional_columns(tables, env_name)
        details = dict(tables=tables, magic_functions=env_details.get('magic_functions', []))
        environment_details[env_name] = details
    print(json.dumps(environment_details, indent=2))

if __name__ == '__main__':
    main()
