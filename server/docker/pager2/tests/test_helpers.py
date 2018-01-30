from pager2.helpers import int_bytes, int_frombytes

def test_int_write():
    assert int_bytes(1, 1) == "\x01"
    assert int_bytes(5, 1) == "\x05"
    assert int_bytes(32, 1) == "\x20"
    assert int_bytes(1, 2) == "\x00\x01"
    assert int_bytes(2047, 2) == "\x07\xff"

def test_int_read():
    assert int_frombytes("\x01") == 1
    assert int_frombytes("\x05") == 5
    assert int_frombytes("\x20") == 32
    assert int_frombytes("\x00\x01") == 1
    assert int_frombytes("\x07\xff") == 2047

