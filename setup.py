from setuptools import setup, find_packages
from version import get_git_version

setup(
    name="htsworkflow",
    version=get_git_version(),
    description="Utilities to help manage high-through-put sequencing",
    author="Diane Trout, Brandon King",
    author_email="diane@caltech.edu",
    packages=find_packages(),
    scripts=[
        "scripts/htsw-copier",
        "scripts/htsw-eland2bed",
        "scripts/htsw-elandseq",
        "scripts/htsw-gerald2bed",
        "scripts/htsw-get-config",
        "scripts/htsw-qseq2fastq",
        "scripts/htsw-record-runfolder",
        "scripts/htsw-runfolder",
        "scripts/htsw-runner",
        "scripts/htsw-spoolwatcher",
        "scripts/htsw-srf",
        "scripts/htsw-srf2fastq",
        "scripts/htsw-update-archive",
        "scripts/htsw-validate",
    ],
    # I should be using one or the other package import
    package_data={
        '': ['*.turtle']
        },
    include_package_data=True,
    install_requires=[
        'distribute',
        'django >=1.7, <1.8',
        'lxml >= 2.2.4',
        'numpy >= 1.6',
        'pandas',
        # 'benderjab >= 0.2',
        'httplib2',
        'keyring',
        'jsonschema',
        'PyLD',
        'requests',
        'six',
        'psycopg2',
        'pytz',
        'rdflib',
        'factory_boy',
    ],
)
