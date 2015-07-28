import yaml
import os.path
import shutil
import subprocess
import sys
from glob import glob

weighted_parts = {
  'tools': ['supervisor', 'nginx'],
  'languages': ['python', 'ruby']
}

class Loader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)
        Loader.add_constructor('!include', Loader.include)

    def include(self, node):
        if   isinstance(node, yaml.ScalarNode):
            return self.extractFile(self.construct_scalar(node))

        elif isinstance(node, yaml.SequenceNode):
            result = []
            for filename in self.construct_sequence(node):
                result += self.extractFile(filename)
            return result

        elif isinstance(node, yaml.MappingNode):
            result = {}
            for k,v in self.construct_mapping(node).iteritems():
                result[k] = self.extractFile(v)
            return result

        else:
            print("Error:: unrecognised node type in !include statement")
            raise yaml.constructor.ConstructorError

    def extractFile(self, filename):
        filepath = os.path.join(self._root, filename)
        with open(filepath, 'r') as f:
            return yaml.load(f, Loader)

languages = {}
for language in glob("sources/languages/*.yml"):
    langname = os.path.basename(language)[:-4]
    languages[langname] = yaml.load(open(language, "r"), Loader)
    languages[langname]['name'] = langname

tools = {}
for tool in glob("sources/tools/*.yml"):
    toolname = os.path.basename(tool)[:-4]
    tools[toolname] = yaml.load(open(tool, "r"), Loader)
    tools[toolname]['name'] = toolname

images = {}
for image in glob("sources/images/*.yml"):
    imagename = os.path.basename(image)[:-4]
    images[imagename] = yaml.load(open(image, "r"), Loader)
    images[imagename]['name'] = imagename

parts = {'tools': tools, 'languages': languages}

def gen_image_part(image, part_type):
    part_list = sorted(list(set.intersection(*map(set,[image[part_type], weighted_parts[part_type]]))), key=weighted_parts[part_type].index)
    part_list += sorted(list(set.difference(*map(set,[image[part_type], weighted_parts[part_type]]))))

    for part_name in part_list:
        part = parts[part_type][part_name]

        if 'packages' in part:
            cleanup_command = part['cleanup_command'] if 'cleanup_command' in part else ''
            image['packages'] = list(set.union(*map(set, [image['packages'], part['packages']])))

        if 'files' in part:
            for image_file in part['files']:
                if not 'scope' in image_file:
                    image_file['scope'] = os.path.join("sources", part_type, part_name)

                image['image_files'].append(image_file)


def fix_recurse_image_dependencies(image):
    # create empty lists
    if not 'languages' in image:
        image['languages'] = []
    if not 'tools' in image:
        image['tools'] = []

    donesomething = True

    # runs until everything is resolved
    while donesomething:
        donesomething = False

        # recurse languages in languages
        for language_name in image['languages']:
            language = languages[language_name]
            if 'languages' in language:
                for sub_language in language['languages']:
                    if not sub_language in image['languages']:
                        image['languages'].append(sub_language)
                        donesomething = True

        # recurse languages in tools
        for tool_name in image['tools']:
            tool = tools[tool_name]
            if 'languages' in tool:
                for sub_language in tool['languages']:
                    if not sub_language in image['languages']:
                        image['languages'].append(sub_language)
                        donesomething = True

        # recurse tools in languages
        for language_name in image['languages']:
            language = languages[language_name]
            if 'tools' in language:
                for sub_tool in language['tools']:
                    if not sub_tool in image['tools']:
                        image['tools'].append(sub_tool)
                        donesomething = True

        # recurse tools in tools
        for tool_name in image['tools']:
            tool = tools[tool_name]
            if 'tools' in tool:
                for sub_tool in tool['tools']:
                    if not sub_tool in image['tools']:
                        image['tools'].append(sub_tool)
                        donesomething = True

def gather_files(image):
    files = []

    for image_file in image['image_files']:
        src = image_file['src']
        srcdir = os.path.dirname(src)
        dst = image_file['dst']

        scope = image_file['scope'] if 'scope' in image_file and not image_file['scope'] == 'image' else "sources/images/%s" % image['name']

        files.append({'src': os.path.join(scope, src), 'dst': dst})

    return files

def parse_image(imagename):
    image = images[imagename]

    if not 'base' in image:
        image['base'] = 'debian'

    if not 'packages' in image:
        image['packages'] = []

    fix_recurse_image_dependencies(image)

    if not 'image_files' in image:
        image['image_files'] = []

    if 'tools' in image:
        gen_image_part(image, 'tools')

    if 'languages' in image:
        gen_image_part(image, 'languages')

    image['image_files'] = gather_files(image)

    return image
