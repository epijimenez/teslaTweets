from setuptools import setup

setup(
    name='teslatweets',
    version='1.1.3',
    py_modules=['teslatweets'],
    python_requires=">=3.9",
    install_requires=["TeslaPy", "googlemaps", "DateTime", "requests_oauthlib", "requests"],
    dependency_links=[
        "https://pypi.org/project/"
    ],
    packages=['teslatweets'],
    include_package_data=True,
    package_dir={'teslatweets': 'teslatweets'},
    package_data={'teslatweets': ['*']},
    entry_points={
        'console_scripts': [
            'teslatweets=teslatweets:main'
        ],
    }
)