import jinja2
import os
import shutil

_ROOT = os.path.abspath(os.path.dirname(__file__))

def template_string(template, values):
    template = os.path.join(_ROOT, template)
    f = open(template, 'r')
    e = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(template))
    )
    t = e.from_string(f.read().decode('utf-8'))
    f.close()

    return t.render(values)

def template_file(template, values, out):
    template = os.path.join(_ROOT, template)
    r = template_string(template, values)

    path = os.path.dirname(out)
    if not os.path.exists(path):
        os.makedirs(path)
    f = open(out, 'w')
    f.write(r.encode('utf-8') + "\n")
    f.truncate()
    f.close()

def template_dir(dir, values, out):
    dir = os.path.join(_ROOT, dir)
    templated_files = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            path = os.path.join(root, name)
            out_path = out + path.replace(dir, '')
            out_dir = os.path.dirname(out_path)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            if name.endswith(".j2"):
                out_path = out_path.replace('.j2', '')
                template_file(path, values, out_path)
            else:
                if os.path.exists(out_path):
                    os.remove(out_path)
                shutil.copy(path, out_path)
            templated_files.append(out_path)
    return templated_files
