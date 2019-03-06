import re
from setuptools import setup, find_packages

with open('seersync/_version.py', 'r') as verFile:
    verContent = verFile.read()
match = re.search(r'^__version__\s*=\s*[\'\"]([^\'\"]*)[\'\"]', verContent, re.MULTILINE)
if not match:
    raise RuntimeError('Failed to parse version file')
ver = match.group(1)

with open("README.md", "r") as readmeFile:
    readme = readmeFile.read()

setup(
    name='seersync',
    version=ver,
    description='Tool to list the changes that rsync would make if a given rsync command line gets executed',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    author='Lenko Grigorov',
    author_email='bnlsw@banica.org',
    url='https://github.com/lenkog/seersync',
    python_requires='>=3.4',
    install_requires=['argparse'],
    license='BSD',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={'console_scripts': ['seersync = seersync.app:main']},
)
