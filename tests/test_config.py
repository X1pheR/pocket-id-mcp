from __future__ import annotations
from pathlib import Path
import pytest
from pocket_id_mcp.config import Settings

def base(tmp_path: Path):
    key=tmp_path/'api-key'; key.write_text('token'); key.chmod(0o600)
    out=tmp_path/'runtime'; out.mkdir(mode=0o700)
    logos=tmp_path/'logos'; logos.mkdir(mode=0o755)
    return key,out,logos

def test_private_paths_are_required(tmp_path: Path) -> None:
    key,out,logos=base(tmp_path); key.chmod(0o644)
    with pytest.raises(ValueError, match='group or other permissions'):
        Settings('https://id.example.test',key,out,10,logos).validate()

def test_secret_file_name_cannot_escape_directory(tmp_path: Path) -> None:
    key,out,logos=base(tmp_path); settings=Settings('https://id.example.test',key,out,10,logos); settings.validate()
    with pytest.raises(ValueError, match='safe basename'): settings.secret_path('../escape')

def test_logo_file_is_bounded_to_configured_directory(tmp_path: Path) -> None:
    key,out,logos=base(tmp_path); (logos/'app.png').write_bytes(b'png')
    settings=Settings('https://id.example.test',key,out,10,logos); settings.validate()
    assert settings.logo_path('app.png') == logos/'app.png'
    with pytest.raises(ValueError, match='safe basename'): settings.logo_path('../app.png')
