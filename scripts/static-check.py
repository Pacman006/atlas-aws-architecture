"""Offline structural validations. Not a replacement for AWS validate-template or deployment."""
from pathlib import Path
import json
import re
import sys
import ast
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'infra' / 'main.yaml'

class CFNLoader(yaml.SafeLoader):
    pass


def load_intrinsic(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        val = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        val = loader.construct_sequence(node)
    else:
        val = loader.construct_mapping(node)
    return {f'Fn::{tag_suffix}': val}

CFNLoader.add_multi_constructor('!', load_intrinsic)


def check_unique_mapping(loader, node, deep=False):
    merged = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in merged:
            raise ValueError(f'duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}')
        merged[key] = loader.construct_object(value_node, deep=deep)
    return merged

CFNLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, check_unique_mapping)


def main():
    doc = yaml.load(TEMPLATE.read_text(), Loader=CFNLoader)
    assert doc['AWSTemplateFormatVersion'] == '2010-09-09'
    resources = doc['Resources']; params = doc['Parameters']
    assert len(resources) >= 50
    assert all(r['Type'].startswith('AWS::') for r in resources.values())
    refs = set(resources) | set(params) | {'AWS::NoValue','AWS::Region','AWS::Partition','AWS::AccountId','AWS::StackName','AWS::StackId'}
    attrs = set(resources)
    misses=[]
    def walk(obj):
        if isinstance(obj,dict):
            if 'Fn::Ref' in obj and obj['Fn::Ref'] not in refs: misses.append(('Ref',obj['Fn::Ref']))
            if 'Fn::GetAtt' in obj:
                val=obj['Fn::GetAtt']
                if isinstance(val,str): key=val.split('.')[0]
                else: key=val[0]
                if key not in attrs: misses.append(('GetAtt',key))
            for v in obj.values(): walk(v)
        elif isinstance(obj,list):
            for v in obj:walk(v)
    walk(doc)
    assert not misses,misses
    # Tests for constraints explicitly stated by the assignment
    text = TEMPLATE.read_text()
    for marker in ('MinSize, Value: \'2\'','MaxSize, Value: \'4\'',
                   'AWS::RDS::DBInstance','AWS::CloudFront::OriginAccessControl',
                   'AWS::Kinesis::Stream','AWS::KinesisFirehose::DeliveryStream',
                   'AWS::CloudWatch::Dashboard','MasterUserSecret.SecretArn'):
        assert marker in text, marker
    py = (ROOT/'backend'/'application.py').read_text()
    compile(py,str(ROOT/'backend'/'application.py'),'exec')
    workflow=yaml.safe_load((ROOT/'.github/workflows/deploy.yml').read_text())
    assert 'jobs' in workflow
    # YAML 1.1 parses 'on' as true; inspect literal source for trigger.
    assert 'branches: [master]' in (ROOT/'.github/workflows/deploy.yml').read_text()
    # Inline transform should be executable without dependencies.
    transform_code = resources['CSVTransformer']['Properties']['Code']['ZipFile']
    compile(transform_code, 'inline-firehose-transform', 'exec')
    ns={};exec(transform_code,ns)
    import gzip,base64
    envelope={'messageType':'DATA_MESSAGE','logEvents':[{'timestamp':1763390000000,'message':json.dumps({'event_type':'http_request','method':'GET','route':'/api/catalog','status':200,'latency_ms':12.8,'request_id':'abc'})}]}
    source=base64.b64encode(gzip.compress(json.dumps(envelope).encode())).decode()
    converted=ns['handler']({'records':[{'recordId':'1','data':source}]},None)['records'][0]
    assert converted['result']=='Ok'
    data=base64.b64decode(converted['data']).decode()
    assert 'GET,/api/catalog,200,12.8,abc,http_request' in data, data
    print('PASS: YAML parsed with distinct keys, CloudFormation local references resolved,')
    print('PASS: 2-4 capacity and primary services found, CI branch master,')
    print('PASS: Python source syntax and CloudWatch gzip → Firehose CSV transformation')
    print('Resource count:',len(resources))
    print('NOTE: Deployment, ACM, IAM and Elastic Beanstalk validation require a real AWS account.')

if __name__=='__main__': main()
