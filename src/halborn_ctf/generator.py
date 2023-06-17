import jinja2
import os
from halborn_ctf import __version__

# with open(os.path.join(os.path.dirname(__file__), 'templates/Dockerfile')) as file_:
#     template = Template(file_.read())
# print(template.render(name='John'))

PYTHON_VERSION = '3.11.2'

generic_template = {
    'Dockerfile': 'Dockerfile.base',
    'challenge.py': 'challenge.base.py'
}

generic_data = {
    'PYTHON_VERSION': PYTHON_VERSION,
    'HALBORN_CTF_VERSION': '.'.join(__version__.split('.', 3)[:3])
}

def generate(templateName: str):
    loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), 'generator'))
    jenv = jinja2.Environment(loader=loader)

    for _file_dst, _template_name in generic_template.items():
        template = jenv.get_template(_template_name)
        data = dict(generic_data, **{
            'name': 'hi'
        })
        out = template.render(data)
        open(_file_dst, 'w').write(out)