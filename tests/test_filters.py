import numpy as np

from pewlib.process import filters


def test_mean_filter_1d():
    np.random.seed(93546376)
    y = np.sin(np.linspace(0, 10, 100))
    y[5::10] += np.random.choice([-1, 1], size=10)

    f = filters.rolling_mean(y, 5, threshold=3.0)
    assert np.all(np.logical_and(-1.0 <= f, f <= 1.0))


def test_mean_filter_2d():
    # Test zeros
    d = np.zeros((10, 10))
    d[5, 5] = 100.0
    f = filters.rolling_median(d, (3, 3), threshold=1.0)
    assert np.all(f == 0.0)

    # Tets random
    np.random.seed(93546376)
    d = np.random.random((50, 50))
    d[5::10, 5::10] += np.random.choice([-2, 2], size=(5, 5))

    f = filters.rolling_mean(d, (5, 5), threshold=3.0)
    assert np.all(np.logical_and(0.0 <= f, f <= 1.0))


def test_median_filter_1d():
    np.random.seed(93546376)
    y = np.sin(np.linspace(0, 10, 100))
    y[5::10] += np.random.choice([-1, 1], size=10)

    f = filters.rolling_mean(y, 5, threshold=3.0)
    assert np.all(np.logical_and(-1.0 <= f, f <= 1.0))


def test_median_filter():
    # Test zeros
    d = np.zeros((10, 10))
    d[5, 5] = 100.0
    f = filters.rolling_median(d, (3, 3), threshold=1.0)
    assert np.all(f == 0.0)

    # Test random
    np.random.seed(93546376)
    d = np.random.random((50, 50))
    d[5::10, 5::10] += np.random.choice([-2, 2], size=(5, 5))

    f = filters.rolling_median(d, (5, 5), threshold=3.0)
    assert np.all(np.logical_and(0.0 <= f, f <= 1.0))
