from continuum.cli import main


def test_main_prints_bootstrap_message(capsys):
    main()
    captured = capsys.readouterr()
    assert "continuum: planning/bootstrap phase" in captured.out
