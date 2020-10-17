import pytest

if __name__ == '__main__':
    # pytest.main(['-q', '--fixtures-per-test'])  # get fixtures in use
    pytest.main(['-s', '--cov', '--color=yes', '../'])  # with coverage report
    # pytest.main(['../', '-s', '--color=yes'])
