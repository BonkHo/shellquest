import pytest

from shellquest import checks


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("7", "7"),
        ("one\ntwo\nthree\n", "three"),
        ("answer\n\n  \n\n", "answer"),
        ("one\r\ntwo\r\n", "two"),
        ("", ""),
        ("\n  \n", ""),
    ],
)
def test_last_line(text: str, expected: str) -> None:
    assert checks.last_line(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("  saffron  ", "saffron"),
        ("Saffron", "saffron"),
        ('"saffron"', "saffron"),
        ("'saffron'", "saffron"),
        ('" saffron "', "saffron"),
        ('"saffron', '"saffron'),  # unbalanced quotes are left alone
        ('"', '"'),
    ],
)
def test_normalize(text: str, expected: str) -> None:
    assert checks.normalize(text) == expected


def test_macos_wc_pads_with_spaces() -> None:
    # macOS `wc -l` prints "       7"; GNU prints "7".
    assert checks.matches_number("       7\n", "7")
    assert checks.matches_text("       7\n", "7")


def test_piped_multi_line_input_uses_the_last_line() -> None:
    piped = "total 3\n.secret-ingredient\nREADME.md\n\nsaffron\n\n"

    assert checks.matches_text(piped, "saffron")
    assert not checks.matches_text(piped, "README.md")


@pytest.mark.parametrize("given", ["BACKUP-OK-7731", "backup-ok-7731\n", ' "Backup-OK-7731" '])
def test_matches_text_accepts(given: str) -> None:
    assert checks.matches_text(given, "BACKUP-OK-7731")


@pytest.mark.parametrize("given", ["", "BACKUP-OK-7732", "BACKUP-OK-7731 please", "saffron"])
def test_matches_text_rejects(given: str) -> None:
    assert not checks.matches_text(given, "BACKUP-OK-7731")


@pytest.mark.parametrize(
    "given", ["187.5", "187.50", "$187.50", " $187.5 ", "187.500\n", '"187.5"']
)
def test_matches_number_ignores_dollar_sign_and_trailing_zeros(given: str) -> None:
    assert checks.matches_number(given, "187.5")


@pytest.mark.parametrize("given", ["7", "07", "7.0", "7.00", "  7\n"])
def test_matches_number_integers(given: str) -> None:
    assert checks.matches_number(given, "7")


@pytest.mark.parametrize(
    "given", ["8", "7.5", "abc", "", "7 files", "nan", "inf", "7e0", "1,000", "--7"]
)
def test_matches_number_rejects(given: str) -> None:
    assert not checks.matches_number(given, "7")


def test_matches_number_rejects_text_expected() -> None:
    # Never let two unparseable values count as equal.
    assert not checks.matches_number("abc", "abc")


@pytest.mark.parametrize(
    "given",
    ["sync.py", "src/pantry/sync.py", "./src/pantry/sync.py", "SRC/Pantry/Sync.py", "'sync.py'"],
)
def test_matches_file_accepts_basename_or_path(given: str) -> None:
    assert checks.matches_file(given, "sync.py")


@pytest.mark.parametrize("given", ["", "mysync.py", "src/pantry/mysync.py", "sync.pyc", "sync"])
def test_matches_file_rejects(given: str) -> None:
    assert not checks.matches_file(given, "sync.py")
