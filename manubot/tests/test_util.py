import manubot.util


def test_shlex_join():
    import pathlib
    args = [
        'command',
        'positional arg',
        'path_arg',
        pathlib.Path('some/path'),
    ]
    output = manubot.util.shlex_join(args)
    assert output == "command 'positional arg' path_arg some/path"
