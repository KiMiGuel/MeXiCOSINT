from mexicosint.cli import build_parser


def test_cli_no_longer_accepts_ip_flag():
    parser = build_parser()

    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert option_strings.isdisjoint({"--" + "ip"})


def test_cli_exposes_mexico_only_mode():
    parser = build_parser()

    args = parser.parse_args(["--mexico-only", "5512345678"])

    assert args.mexico_only is True
    assert args.number == "5512345678"


def test_cli_accepts_batch_file():
    parser = build_parser()

    args = parser.parse_args(["--batch", "numbers.txt"])

    assert args.batch == "numbers.txt"
    assert args.number is None


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
