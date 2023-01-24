import setuptools


with open('readme.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='md.event',
    version='1.0.0',
    description='Event dispatcher',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='License :: OSI Approved :: MIT License',
    package_dir={'': 'lib'},
    packages=['md.event'],
    install_requires=['md.python==1.*', 'psr.event==1.*'],
    dependency_links=[
        'https://source.md.land/python/md-python/'
        'https://source.md.land/python/psr-event/'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
