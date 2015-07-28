import shelve
import dockerfactory.packages
import dockerfactory.images
import dockerfactory.baseimage
import dockerfactory.files
import dockerfactory.sourceparser

d = shelve.open(".containers")
repo_pkgs = dockerfactory.packages.get_repo_pkg_versions()
seen_images = []

def check_base_image():
    if not 'debian' in d or (not dockerfactory.images.exists(d['debian']['id'])) or len(dockerfactory.packages.check_for_updates(d['debian']['packages'], repo_pkgs)) or dockerfactory.files.get_latest_file_change([{'src': "dockerfactory/baseimage.py"}]) > d['debian']['created']:
        base_image = dockerfactory.baseimage.build_base_image()
        d['debian'] = {
            'id': base_image,
            'packages_image': base_image,
            'packages': dockerfactory.packages.get_pkg_versions(base_image),
            'created': dockerfactory.images.get_image_date(base_image)
        }
    else:
        print(":: debian is up to date! (%d packages)" % len(d['debian']['packages']))


def build_images(images):
    global built_images

    for image_name in images:
        if image_name in seen_images:
            continue
        seen_images.append(image_name)

        image = dockerfactory.sourceparser.parse_image("nginx")

        # build dependencies
        if not image['base'] == 'debian':
            build_images([image['base']])

        # full rebuild
        full_rebuild = False
        files_rebuild = False
        if not image_name in d or not 'id' in d[image_name]:
            full_rebuild = True
        elif d[image['base']]['created'] > d[image_name]['created']:
            full_rebuild = True
        elif len(dockerfactory.packages.check_for_updates(d[image_name]['packages'], repo_pkgs)) > 0:
            full_rebuild = True
        elif dockerfactory.files.get_latest_file_change(image['image_files']) > d[image_name]['created']:
            files_rebuild = True

        if not image_name in d:
            d[image_name] = {}

        new_spec = d[image_name]

        if full_rebuild:
            print(":: Rebuilding %s (full)" % image_name)
            if set(d[image['base']]['packages']).issuperset(set(image['packages'])):
                print("   -> Base image already has all packages, reusing image")
                new_spec['packages_image'] = d[image['base']]['id']
                new_spec['packages'] = d[image['base']]['packages']
            else:
                print("   -> Installing packages...")
                package_image = dockerfactory.images.install_packages(d[image['base']]['id'], image['packages'])
                new_spec['packages_image'] = package_image
                new_spec['packages'] = dockerfactory.packages.get_pkg_versions(package_image)
                print("   -> %d packages installed (%d total)" % (len(new_spec['packages']) - len(d[image['base']]['packages']), len(new_spec['packages'])))

            files_rebuild = True

        if files_rebuild:
            if not full_rebuild:
                print(":: Rebuilding %s (files only)" % image_name)

            print("   -> Adding files...")
            files_image = dockerfactory.images.add_files(new_spec['packages_image'], image['image_files'])
            new_spec['id'] = files_image
            new_spec['created'] = dockerfactory.images.get_image_date(files_image)

            print("   -> Tagging image...")
            dockerfactory.images.tag_image(new_spec['id'], image_name)

            print("   -> Pushing image...")
            dockerfactory.images.push_image(image_name)

        if not files_rebuild:
            print(":: %s is up to date! (%d packages)" % (image_name, len(new_spec['packages'])))

        d[image_name] = new_spec

def build(image=None):
    check_base_image()
    build_images(dockerfactory.sourceparser.images)
    d.close()

