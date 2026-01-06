from core.classes.Config import Config

def test_config_getitem(monkeypatch):
    monkeypatch.setattr('core.classes.Config.load_config', lambda: {'foo': 'bar'})
    config = Config()
    assert config['foo'] == 'bar'

def test_config_get(monkeypatch):
    monkeypatch.setattr('core.classes.Config.load_config', lambda: {'foo': 'bar'})
    config = Config()
    assert config.get('foo') == 'bar'
    assert config.get('baz', 123) == 123

def test_config_as_dict(monkeypatch):
    monkeypatch.setattr('core.classes.Config.load_config', lambda: {'foo': 'bar'})
    config = Config()
    assert config.as_dict() == {'foo': 'bar'}
