from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

setup(
    name='networktest',
    description='Tools for testing applications that make network requests.',
    long_description=readme,
    packages=find_packages(exclude=['tests']),
    use_scm_version=True,
    author='Matt Wisniewski',
    author_email='mattw@jwplayer.com',
    url='https://github.com/jwplayer/networktest',
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
        'pytest-flake8',
        'pytest-cov',
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Pytest',
    ],
    entry_points={
        'pytest11': ['networktest = networktest.pytest.plugin']
    },
)
