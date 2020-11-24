from setuptools import setup

setup(
    name='kskp.engine',
    packages=['kskp.engine'],
    description='Core Engine for Flow-base Data Processing',
    url='https://www.kskp.io',
    install_requires=[
        # 0.10.1ではインスコ時にpathtoolsが入らない
        'watchdog==0.9.0'
    ],
)
