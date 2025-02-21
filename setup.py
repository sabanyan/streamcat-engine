from setuptools import setup

setup(
    name='streamcat.engine',
    packages=['streamcat.engine'],
    version='3.5',
    description='Core Engine for Flow-base Data Processing',
    url='https://www.kskp.io',
    install_requires=[
        # 0.10.1ではインスコ時にpathtoolsが入らない
        'watchdog'
    ],
)
