from setuptools import setup, find_packages
setup(
    name="compare-targets",
    version="1.0.0",
    description='A simple utility for comparing targets within Xcode projects',
    author="Sixten Otto",
    author_email="opensource@sfko.com",

    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Operating System :: MacOS :: MacOS X',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Quality Assurance',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.11',
    ],

    packages=find_packages(),
    install_requires=[
        "click",
        "pbxproj",
    ],

    entry_points={
        "console_scripts": [
            "compare-targets=compare-targets:main",
        ],
    }
)
