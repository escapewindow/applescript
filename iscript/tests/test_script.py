#!/usr/bin/env python
# coding=utf-8
"""Test iscript.script
"""
import os
import pytest
from iscript.exceptions import IScriptError
import iscript.script as script


# async_main {{{1
@pytest.mark.parametrize('behavior, raises', ((
    'mac_pkg', False
), (
    'mac_notarize', False
), (
    None, False,
), (
    'invalid_behavior', True
)))
@pytest.mark.asyncio
async def test_async_main(mocker, behavior, raises):
    """``async_main`` calls ``sign_and_notarize_all``.

    """

    notarize_calls = []
    pkg_calls = []
    config = {'a': 'b'}
    task = {'c': 'd', 'payload': {}}
    if behavior:
        task['payload']['behavior'] = behavior
    expected = [[(config, task), {}]]

    async def test_notarize(*args, **kwargs):
        notarize_calls.append([args, kwargs])

    async def test_pkg(*args, **kwargs):
        pkg_calls.append([args, kwargs])

    mocker.patch.object(script, 'sign_and_notarize_all', new=test_notarize)
    mocker.patch.object(script, 'create_and_sign_all_pkg_files', new=test_pkg)
    if raises:
        with pytest.raises(IScriptError):
            await script.async_main(config, task)
    else:
        await script.async_main(config, task)
        if behavior == 'mac_notarize':
            assert notarize_calls == expected
        else:
            assert pkg_calls == expected


# get_default_config {{{1
def test_get_default_config(tmpdir):
    """``get_default_config`` returns a dict with expected keys/values.

    """
    config = script.get_default_config(base_dir=tmpdir)
    assert config['work_dir'] == os.path.join(tmpdir, 'work')
    for k in ('artifact_dir', 'schema_file'):
        assert k in config


# main {{{1
@pytest.mark.asyncio
async def test_main(mocker):
    """``main`` calls ``sync_main`` with ``async_main`` and ``default_config``.

    This function is async because we have an async helper function inside.
    """

    calls = []
    config = {'a': 'b'}

    def fake_main(*args, **kwargs):
        calls.append([args, kwargs])

    def fake_config():
        return config

    async def fake_async_main(*args, **kwargs):
        pass

    mocker.patch.object(script, 'sync_main', new=fake_main)
    mocker.patch.object(script, 'async_main', new=fake_async_main)
    mocker.patch.object(script, 'get_default_config', new=fake_config)
    script.main()
    assert calls == [[(fake_async_main, ), {'default_config': config}]]