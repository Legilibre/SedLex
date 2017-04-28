import jinja2
import os

def template_string(template, values):
    f = open(template, 'r')
    e = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(template))
    )
    t = e.from_string(f.read().decode('utf-8'))
    f.close()

    return t.render(values)

def template_file(template, values, out):
    r = template_string(template, values)

    path = os.path.dirname(out)
    if not os.path.exists(path):
        os.makedirs(path)
    f = open(out, 'w')
    f.write(r.encode('utf-8'))
    f.truncate()
    f.close()
