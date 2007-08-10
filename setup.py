from setuptools import setup

setup(
  name="uashelper",
  description="some bots and other utilities to help deal with data from an illumina sequencer",
  author="Diane Trout",
  author_email="diane@caltech.edu",
  packages=["uashelper"],
  scripts=['scripts/spoolwatcher', 'scripts/copier'],
)
