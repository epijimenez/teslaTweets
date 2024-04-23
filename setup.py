from setuptools import setup
import teslatweet

setup(
    name='teslatweet',
    version='0.2.3',
    py_modules=['teslatweet'],
    python_requires=">=3.9",
    install_requires=["teslapy", "googlemaps", "datetime", "requests_oauthlib", "requests"],
    dependency_links=[
        "https://pypi.org/project/"
    ],
    entry_points={
        'console_scripts': [
            'teslatweet=teslatweet:main'
        ],
    }
)