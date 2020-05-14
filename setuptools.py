from setuptools import setup

setup(
    name='snapshotalyzer-30000',
    version='1.0',
    author='Jeremy Greer',
    author_email='jex.grizzle@gmail.com,
    description='manage aws ec2 snapshots',
    packages=[
        'shotty'
    ],
    url='https://github.com/reergymerej/snapshotalyzer-30000',
    install_requires=[
        'click',
        'boto3',
    ],
    entry_points='''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',
)
