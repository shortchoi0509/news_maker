from setuptools import setup, find_packages

_install_dependencies = [
    'setuptools',
    'requests',
    'newspaper3k',
    'beautifulsoup4',
    'lxml',
    'lxml_html_clean',
    'openai',
    'IPython',
    'ipywidgets',
    'markdown'
]

setup(
    name='podcast-maker',
    version='0.0.1',
    packages=find_packages(),
    install_requires=_install_dependencies,
    setup_requires=['pytest-runner'],
    tests_require=['pytest==8.3.2', 'iniconfig==2.0.0'],
    python_requires='>=3.10',
)
