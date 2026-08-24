from __future__ import annotations
import stat
from pathlib import Path
from typing import Any
import pytest
from pocket_id_mcp.config import Settings
from pocket_id_mcp.models import RestrictedClientCreateInput
from pocket_id_mcp.service import PocketIdService

class FakeClient:
    def __init__(self) -> None:
        self.created_payload=None; self.allowed_payload=None; self.deleted=False
        self.secret='super-secret-value'; self.secret_id='secret-2'; self.logo_uploads=[]
        self.secrets=[{'id':'secret-1','prefix':'old1','createdAt':'2026-08-01T00:00:00Z','expiresAt':None,'isActive':True}]
        self.client={'id':'client-1','name':'Proxmox VE','callbackURLs':['https://proxmox.example.test'],'logoutCallbackURLs':[],'isPublic':False,'pkceEnabled':False,'requiresReauthentication':False,'launchURL':None,'isGroupRestricted':True,'allowedUserGroups':[{'id':'group-1','name':'admins','friendlyName':'Admins'}],'hasLogo':False,'hasDarkLogo':False}
    def list_paginated(self,path:str,*,search=None):
        if path=='/api/user-groups': return [{'id':'group-1','name':'admins','friendlyName':'Admins'}]
        if path=='/api/oidc/clients': return []
        raise AssertionError(path)
    def request(self,method,path,payload=None,*,authenticated=True):
        if method=='POST' and path=='/api/oidc/clients': self.created_payload=dict(payload); return {'id':'client-1'}
        if method=='PUT' and path.endswith('/allowed-user-groups'): self.allowed_payload=dict(payload); return self.client
        if method=='GET' and path=='/api/oidc/clients/client-1': return self.client
        if method=='GET' and path=='/api/oidc/clients/client-1/secrets': return list(self.secrets)
        if method=='POST' and path=='/api/oidc/clients/client-1/secrets':
            item={'id':self.secret_id,'prefix':'supe','createdAt':'2026-08-24T00:00:00Z','expiresAt':None,'isActive':True,'secret':self.secret}; self.secrets.append({k:v for k,v in item.items() if k!='secret'}); return item
        if method=='DELETE' and path.startswith('/api/oidc/clients/client-1/secrets/'):
            sid=path.rsplit('/',1)[-1]; self.secrets=[x for x in self.secrets if x['id']!=sid]; return None
        if method=='DELETE' and path=='/api/oidc/clients/client-1': self.deleted=True; return None
        if method=='DELETE' and path.startswith('/api/oidc/clients/client-1/logo?'):
            light=path.endswith('true'); self.client['hasLogo' if light else 'hasDarkLogo']=False; return None
        raise AssertionError((method,path,payload))
    def upload_file(self,path,*,field_name,file_name,content_type,data):
        self.logo_uploads.append((path,field_name,file_name,content_type,len(data)))
        self.client['hasLogo' if path.endswith('true') else 'hasDarkLogo']=True
        return None

def make_settings(tmp_path:Path)->Settings:
    key=tmp_path/'api-key'; key.write_text('test-token'); key.chmod(0o600)
    out=tmp_path/'runtime'; out.mkdir(mode=0o700)
    logos=tmp_path/'logos'; logos.mkdir(mode=0o755)
    return Settings('https://id.example.test',key,out,10,logos)

def test_create_restricted_client_verifies_exact_groups(tmp_path):
    fake=FakeClient(); service=PocketIdService(fake,make_settings(tmp_path))
    result=service.create_restricted_client(RestrictedClientCreateInput(name='Proxmox VE',callback_urls=['https://proxmox.example.test'],allowed_group_names=['admins']))
    assert result['isGroupRestricted'] is True; assert fake.created_payload['isGroupRestricted'] is True; assert fake.allowed_payload=={'userGroupIds':['group-1']}; assert fake.deleted is False

def test_create_restricted_client_rolls_back_failed_postcondition(tmp_path):
    fake=FakeClient(); fake.client['isGroupRestricted']=False; service=PocketIdService(fake,make_settings(tmp_path))
    with pytest.raises(Exception,match='not group restricted'): service.create_restricted_client(RestrictedClientCreateInput(name='Proxmox VE',callback_urls=['https://proxmox.example.test'],allowed_group_names=['admins']))
    assert fake.deleted is True

def test_secret_is_added_written_and_not_returned(tmp_path):
    fake=FakeClient(); settings=make_settings(tmp_path); service=PocketIdService(fake,settings)
    result=service.create_secret_file('client-1','proxmox-secret'); path=settings.secret_output_dir/'proxmox-secret'
    assert path.read_text()==fake.secret; assert stat.S_IMODE(path.stat().st_mode)==0o600; assert fake.secret not in repr(result); assert result['secret_id']=='secret-2'; assert len(fake.secrets)==2

def test_secret_list_and_guarded_delete(tmp_path):
    fake=FakeClient(); service=PocketIdService(fake,make_settings(tmp_path))
    assert service.list_client_secrets('client-1')[0]['id']=='secret-1'
    with pytest.raises(ValueError,match='confirm'): service.delete_client_secret('client-1','secret-1',False)
    result=service.delete_client_secret('client-1','secret-1',True); assert result['deleted'] is True; assert fake.secrets==[]

def test_secret_file_refuses_overwrite_without_creating_secret(tmp_path):
    fake=FakeClient(); settings=make_settings(tmp_path); target=settings.secret_output_dir/'existing'; target.write_text('keep'); target.chmod(0o600); service=PocketIdService(fake,settings)
    with pytest.raises(FileExistsError): service.create_secret_file('client-1','existing')
    assert target.read_text()=='keep'; assert len(fake.secrets)==1

def test_logo_upload_and_delete_are_bounded(tmp_path):
    fake=FakeClient(); settings=make_settings(tmp_path); (settings.logo_input_dir/'app.png').write_bytes(b'fakepng'); service=PocketIdService(fake,settings)
    result=service.upload_client_logo('client-1','app.png',True); assert result['uploaded'] is True; assert fake.logo_uploads[0][0].endswith('light=true'); assert fake.client['hasLogo'] is True
    with pytest.raises(ValueError,match='confirm'): service.delete_client_logo('client-1',True,False)
    assert service.delete_client_logo('client-1',True,True)['deleted'] is True; assert fake.client['hasLogo'] is False
