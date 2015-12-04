from setuptools import setup, find_packages  # type: ignore

setup(
    name='tryp',
    description='tryp tools',
    version='1.0.1',
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/tryp',
    packages=find_packages(exclude=['unit', 'unit.*']),
    install_requires=[
        'tek',
        'fn',
        'toolz',
    ]
)
