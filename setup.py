from setuptools import setup, find_packages


# Read requirements/test_requirements
def filter_options(req):
    return not req.strip().startswith('--')


test_requirements = []
try:
    with open('test-requirements.txt') as file_handle:
        test_requirements = list(filter(filter_options, file_handle.read().splitlines()))
except FileNotFoundError as exc:
    pass

setup(
    name="jackbot",
    version="1.0.0",
    description="Jackbox game results retriever",
    long_description="Pull results from various completed jackbox games and push them to slack channel(s)",
    author='Jacob Truman',
    author_email='jatruman@adobe.com',
    url='https://gitlab.com/jacobtruman/jackbot',
    packages=find_packages(),
    package_data={},
    zip_safe=False,
    install_requires=[
        "svgwrite",
        "cairosvg",
        "slackclient",
        "requests",
    ],
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'jackbot=bin.jackbot:main'
        ],
    },
    dependency_links=[],
)
