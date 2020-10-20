from setuptools import setup

setup(
    name='kskp.engine',
    packages=['kskp.engine'],
    description='Core Engine for Flow-base Data Processing',
    url='https://www.ksk-anl.com/products/kskp',
    version_config={
        'version_format': '{tag}',
        'starting_version': '2.0.0'
    },
    setup_requires=['better-setuptools-git-version'],
    install_requires=[
        # 0.10.1ではインスコ時にpathtoolsが入らない
        'watchdog==0.9.0'
    ],
)
