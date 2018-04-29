# By Janos Potecki
# University College London
# January 2018


from awslambdacontinuousdelivery.python.build.resources import *

from troposphere import GetAtt, Template

import awacs.aws

from typing import Tuple
Key = str
Bucket = str

def getBuild( template: Template
            , repo_code: str
            , interimName: str
            , outputName: str
            , stages: List[str]
            ) -> Stages:
  role = getBuildRole()
  if role.title not in template.resources:
    role = template.add_resource(role)
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
