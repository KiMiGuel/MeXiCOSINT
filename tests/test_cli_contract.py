from mexicosint.cli import build_parser


def test_cli_no_longer_accepts_ip_flag():
    parser = build_parser()

    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert option_strings.isdisjoint({"--" + "ip"})


def test_cli_keeps_dummy_test_flag():
    parser = build_parser()

    assert "--dummy-test" in parser.format_help()
