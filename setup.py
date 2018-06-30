#!/usr/bin/env python

from distutils.core import setup

setup( name='pyAwsLambdaBuild'
     , version = '0.0.2'
     , description = 'pyAwsLambdaBuild'
     , author = 'Janos Potecki'
     , url = 'https://github.com/AwsLambdaContinuousDelivery/pyAwsLambdaBuild'
     , packages = ['awslambdacontinuousdelivery.python.build']
     , license='MIT'
     , install_requires = [ 
          'troposphere'
        , 'awacs'
        ]
     )
