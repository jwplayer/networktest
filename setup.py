from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

setup(
    name='nettest',
    description='Tools for testing applications that make network requests.',
    long_description=readme,
    packages=find_packages(exclude=['tests']),
    use_scm_version=True,
    author='Matt Wisniewski',
    author_email='mattw@jwplayer.com',
    url='https://github.com/jwplayer/nettest',
    keywords=[
        'network',
        'test',
        'functional',
        'unit',
        'integration',
        'api',
        'http',
        'request'
    ],
    license='Apache License 2.0',
    setup_requires=[
        'pytest-runner',
        'setuptools_scm',
    ],
    tests_require=[
        'pytest',
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
)