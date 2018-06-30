
from awslambdacontinuousdelivery.tools.iam import defaultAssumeRolePolicyDocument
from awslambdacontinuousdelivery.tools import alphanum

from troposphere import Template, Ref, Sub, Join
from troposphere.codebuild import ( Project
  , Environment, Source, Artifacts )
from troposphere.codepipeline import ( InputArtifacts
  , Actions, Stages, ActionTypeId, OutputArtifacts )
from troposphere.iam import Role, Policy

from typing import List, Tuple

Bucket = str
Key = str

import awacs.aws
from awacs.aws import Statement, Action, Allow
def getBuildRole() -> Role:
  statement = Statement( Action = [ Action("*") ]
                       , Effect = Allow
                       , Resource = ["*"]
                       )
  policy_doc = awacs.aws.Policy( Statement = [ statement ] )
  policy = Policy( PolicyName = Sub("${AWS::StackName}-CodeBuildPolicy")
                 , PolicyDocument = policy_doc
                 )
  assume = defaultAssumeRolePolicyDocument("codebuild.amazonaws.com")
  return Role( "CodeBuildRole"
             , RoleName = Sub("${AWS::StackName}-LambdaCodeBuildRole")
             , AssumeRolePolicyDocument = assume
             , Policies = [policy]
             )


def getDockerBuildAction( buildRef
                        , inputs: List[str]
                        , outputs: List[str]
                        , number = 1
                        ) -> Actions:
  '''
  Takes a build reference which points to the build configuration,
  input/output map with the names of the artifacts and (optimal) a number,
  if multiple build actions must be added to the same pipeline
  '''
  number = str(number)
  inputArts  = map(lambda x: InputArtifacts( Name = x ), inputs)
  outputArts = map(lambda x: OutputArtifacts( Name = x), outputs)
  actionId = ActionTypeId( Category = "Build"
                         , Owner = "AWS"
                         , Version = "1"
                         , Provider = "CodeBuild"
                         )
  return Actions( Name = Sub("${AWS::StackName}-BuildAction" + number)
                , ActionTypeId = actionId
                , InputArtifacts = list(inputArts)
                , OutputArtifacts = list(outputArts)
                , RunOrder = number
                , Configuration = { "ProjectName" : Ref(buildRef) }
                )


def getCodeBuild( name: str
                , serviceRole: Role
                , buildspec: List[str]
                ) -> Project:
  env = Environment( ComputeType = "BUILD_GENERAL1_SMALL"
                   , Image = "frolvlad/alpine-python3"
                   , Type = "LINUX_CONTAINER"
                   , PrivilegedMode = False
                   )
  source = Source( Type = "CODEPIPELINE"
                 , BuildSpec = Join("\n", buildspec)
                 )
  artifacts = Artifacts( Type = "CODEPIPELINE" )
  return Project( alphanum(name)
                , Name = Sub("${AWS::StackName}-" + alphanum(name))
                , Environment = env
                , Source = source
                , Artifacts = artifacts
                , ServiceRole = Ref(serviceRole)
                )


def generateCloudFormationSpec() -> List[str]:
  return [ "version: 0.2"
         , "\n"
         , "phases:"
         , "  install:"
         , "    commands:"
         , "      - apk add --no-cache bash git openssl"
         , "  pre_build:"
         , "    commands:"
         , "      - pip3 install troposphere"
         , "      - pip3 install awacs"
         , "      - git clone https://github.com/AwsLambdaContinuousDelivery/AwsLambdaContinuousDeliveryTools.git"
         , "      - cd AwsLambdaContinuousDeliveryTools"
         , "      - pip3 install ."
         , "      - cd .."
         , "      - rm -rf AwsLambdaContinuousDeliveryTools"
         , "      - wget https://raw.githubusercontent.com/AwsLambdaContinuousDelivery/AwsLambdaContinuousDeliveryLambdaCfGenerator/v2/createCF.py"
         , "  build:"
         , "    commands:"
         ]


def generateDeploymentPackageSpec() -> List[str]:
  return [ "version: 0.2"
         , "phases:"
         , "  install:"
         , "    commands:"
         , "      - pip3 install --upgrade pip setuptools"
         , "  build:"
         , "    commands:"
         , "      - pip3 install -r requirements.txt -t ."
         , "      - ls -a"
         , "      - mv -v src/* ."
         , "      - rm -rf src"
         , "      - rm -rf config"
         , "      - rm -rf test"
         , "      - ls -a"
         , "artifacts:"
         , "  type: zip"
         , "  files:"
         , "    - '**/*'"
         ]


def getBuildSpec(stages: List[str]) -> List[str]:
  file_code = generateCloudFormationSpec()
  stage_cmds = []
  for s in stages:
    x = Join(" ", [ "      - python3 createCF.py --path $(pwd)/ --stage"
                  , s.capitalize()
                  , "--stack"
                  , Sub("${AWS::StackName}")
                  , ">> stack" + s.capitalize() + ".json"
                  ]
         )
    stage_cmds.append(x)

  prod = Join(" ", [ "      - python3 createCF.py --path $(pwd)/ --stage"
                   , "PROD --stack"
                   , Sub("${AWS::StackName}")
                   , ">> stackPROD.json"
                   ]
             )
  stage_cmds.append(prod)
  build_cmd = Join("\n", stage_cmds)
  artifacts = [ "artifacts:"
              , "  files:"
              , "    - stackPROD.json"
              ]
  for s in stages:
    artifacts.append("    - stack" + s.capitalize() + ".json")
  artifacts = Join("\n",artifacts)

  file_code.append("\n")
  file_code.append(build_cmd)
  file_code.append("\n")
  file_code.append(artifacts)
  return file_code


def getDeploymentBuilder(role: Role) -> Action:
  deploySpec = generateDeploymentPackageSpec()
  return getCodeBuild("DeployPkgBuilder", role, deploySpec)

def getCloudFormationBuilder( role: Role
                            , stages: List[str]
                            ) -> Actions:
  cfSpec = getBuildSpec(stages)
  return getCodeBuild("cfBuilder", role, cfSpec)
