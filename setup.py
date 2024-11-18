from setuptools import setup

setup(
    name='teslatweet',
    version='1.1.0',
    py_modules=['teslatweet'],
    python_requires=">=3.9",
    install_requires=["TeslaPy", "googlemaps", "DateTime", "requests_oauthlib", "requests"],
    dependency_links=[
        "https://pypi.org/project/"
    ],
    packages=['teslatweet'],
    include_package_data=True,
    package_dir={'teslatweet': 'teslatweet'},
    package_data={'teslatweet': ['*']},
    entry_points={
        'console_scripts': [
            'teslatweet=teslatweet:main'
        ],
    }
)