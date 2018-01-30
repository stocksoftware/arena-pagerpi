from setuptools import setup, find_packages

setup(
    name="pager2",
    version="0.1",
    description="Pager status website.",
    packages=['pager2'],
    package_data={'pager2': ['*.html']},
    install_requires=["twisted>=17.9.0",
                      "Jinja2>=2.10",
                      "SQLAlchemy>=1.2.1"],
#                      "service_identity>=14.0.0"],
    entry_points={'console_scripts':
                  ['pager-site = pager2.main:main']}
)
