import numpy as np

from pew.lib import calc


def test_greyscale_to_rgb():
    grey = calc.greyscale_to_rgb(np.linspace(0, 1, 5), [128, 256, 256])
    assert np.allclose(
        grey, [[0, 0, 0], [32, 64, 64], [64, 128, 128], [96, 192, 192], [128, 256, 256]]
    )


def test_kmeans():
    x = np.empty((100, 2), dtype=float)
    x[:50, 0] = np.random.normal(loc=-1.0, size=50)
    x[50:, 0] = np.random.normal(loc=1.0, size=50)
    x[:, 1] = np.random.normal(loc=3.0, size=100)

    x = np.random.random(100)
    y = np.zeros(100)
    y[50:] += 1.0
    y[80:] += 1.0

    idx = calc.kmeans(np.stack((x, y), axis=1), 3, init="kmeans++")
    _, counts = np.unique(idx, return_counts=True)
    assert np.allclose(np.sort(counts), [20, 30, 50], atol=5)
    idx = calc.kmeans(np.stack((x, y), axis=1), 3, init="random")
    _, counts = np.unique(idx, return_counts=True)
    assert np.allclose(np.sort(counts), [20, 30, 50], atol=10)


def test_local_maxima():
    x = np.linspace(0.0, 1.0, 100)
    i = np.arange(5, 95, 5)
    x[i] = 10.0
    assert np.all(calc.local_maxima(x)[:-1] == i)


def test_normalise():
    x = np.random.random(100)
    x = calc.normalise(x, -1.0, 2.33)
    assert x.min() == -1.0
    assert x.max() == 2.33


def test_shuffle_blocks():
    x = np.random.random((100, 100))
    m = np.zeros((100, 100))
    m[:52] = 1.0

    y = calc.shuffle_blocks(x, (5, 20), mask=m, mask_all=True)

    assert np.allclose(y[50:], x[50:])
    assert not np.allclose(y[:50], x[:50])
    assert np.allclose(y.sum(), x.sum())


def test_sliding_window():
    x = np.arange(10)
    w = calc.sliding_window(x, 3)
    assert np.all(np.mean(w, axis=1) == [1, 2, 3, 4, 5, 6, 7, 8])
    w = calc.sliding_window_centered(x, 3)
    assert np.all(np.mean(w, axis=1) == [1 / 3.0, 1, 2, 3, 4, 5, 6, 7, 8, 26 / 3.0])


def test_subpixel_offset():
    x = np.ones((10, 10, 3))

    y = calc.subpixel_offset(x, [(0, 0), (1, 1), (2, 3)], (2, 3))
    assert y.shape == (22, 33, 3)
    assert np.all(y[0:20, 0:30, 0] == 1)
    assert np.all(y[1:21, 1:31, 1] == 1)
    assert np.all(y[2:22, 3:33, 2] == 1)

    assert np.all(
        calc.subpixel_offset(x, [(0, 0), (1, 1)], (2, 2))
        == calc.subpixel_offset_equal(x, [0, 1], 2)
    )
