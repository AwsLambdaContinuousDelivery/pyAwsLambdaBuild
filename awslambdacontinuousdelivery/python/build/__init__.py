
from awslambdacontinuousdelivery.python.build.resources import *

from troposphere import GetAtt, Template

import awacs.aws

from typing import Tuple
Key = str
Bucket = str

def buildStage( template: Template 
              , repo_code: str
              , interimName: str
              , outputName: str
              , stages: List[str]
              ) -> Stages: #TODO continue here
              # We need to add the parameter overrides to the deployment of the 
              # lambda function and not to the other crap
  role = template.add_resource(getBuildRole())
  artBuilder = getDeploymentBuilder(role)
  artBuilderRef = template.add_resource(artBuilder)
  funcBuilder = getCloudFormationBuilder(role, stages)
  funcBuilderRef = template.add_resource(funcBuilder)
  a1 = getDockerBuildAction(artBuilder, [repo_code], [interimName], 1)
  a2 = getDockerBuildAction(funcBuilder, [repo_code], [outputName], 2)
  return Stages( "BuildStage"
               , Name = "Build"
               , Actions = [ a1, a2 ]
               )