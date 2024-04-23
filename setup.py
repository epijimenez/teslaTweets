from setuptools import setup
import teslatweet

setup(
    name='teslatweet',
    version='0.2.1',
    py_modules=['teslatweet'],
    install_requires=["teslapy", "googlemaps", "datetime"],
    dependency_links=[
        "https://pypi.org/project/"
    ],
    entry_points={
        'console_scripts': [
            'teslatweet=teslatweet:main'
        ],
    }
)