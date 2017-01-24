from setuptools import setup, find_packages

setup(
    name='zones',
    version='0.1.0b',
    description='Generation of Bind zonefiles.',
    url='http://github.com/mikeboers/zones',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    include_package_data=True,
    
    author='Mike Boers',
    author_email='zones@mikeboers.com',
    license='BSD-3',
    
    entry_points={
        'console_scripts': [

        ],
    },
    
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)