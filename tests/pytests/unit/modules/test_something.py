import io
import salt.utils.files
from tests.support.mock import create_autospec, patch, MagicMock

__utils__ = {'files.fopen': salt.utils.files.fopen}


def write_the_first_three_primes_to_a_file():
    with salt.utils.files.fopen('/tmp/primes.txt', 'w') as f:
        f.write('2,3,5')


def write_the_first_three_primes_to_a_file_using_dunder_utils():
    with __utils__['files.fopen']('/tmp/other-primes.txt', 'w') as f:
        f.write('2,3,5')


def test_boop():
    expected_primes = '2,3,5'

    file_one = io.StringIO()
    orig_close = file_one.close
    file_one.close = MagicMock()
    patch_func = patch('salt.utils.files.fopen', autospec=True, return_value=file_one)
    with patch_func:
        write_the_first_three_primes_to_a_file()

    assert file_one.getvalue() == expected_primes
    orig_close()


    file_two = io.StringIO()
    file_two.close = MagicMock()
    fake_fopen = create_autospec(salt.utils.files.fopen, return_value=file_two)
    patch_dict = patch.dict(__utils__, {'files.fopen': fake_fopen})
    with patch_dict:
        write_the_first_three_primes_to_a_file_using_dunder_utils()

    assert file_two.getvalue() == expected_primes
