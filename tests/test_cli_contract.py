from mexicosint.cli import build_parser


def test_cli_no_longer_accepts_ip_flag():
    parser = build_parser()

    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert option_strings.isdisjoint({"--" + "ip"})


def test_cli_keeps_dummy_test_flag_but_hides_it_from_help():
    """--dummy-test stays functional for internal debugging, but isn't
    documented publicly (not in --help, README, or docs/)."""
    parser = build_parser()

    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert "--dummy-test" in option_strings
    assert "--dummy-test" not in parser.format_help()
