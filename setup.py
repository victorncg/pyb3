from setuptools import setup

setup(
   name='pyb3',
   version='1.0',
   description='Realiza análises financeiras',
   author='Fábio Teixeira',
   author_email='fabiomt92@hotmail.com',
   packages=['pyb3', 'pyb3.crawler'],  #same as name
   install_requires=['bs4', 'requests'], #external packages as dependencies
)







