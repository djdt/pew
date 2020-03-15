import numpy as np

from pew.calc import cwt, local_extrema, ricker_wavelet, sliding_window_centered


def _identify_ridges(
    cwt_coef: np.ndarray, windows: np.ndarray, gap_threshold: int = None, mode="maxima",
) -> np.ndarray:
    if gap_threshold is None:
        gap_threshold = len(windows) // 4

    ridges = np.array([], dtype=int).reshape(0, cwt_coef.shape[0])

    for i in np.arange(cwt_coef.shape[0] - 1, -1, -1):
        extrema = local_extrema(cwt_coef[i], windows[i] * 2, mode=mode)

        for ridge in ridges:
            # Skip already gapped ridges
            if np.count_nonzero(ridge[i + 1 :] == -1) > gap_threshold:
                continue

            diffs = np.abs(extrema - ridge[i + 1])
            min_diff = np.argmin(diffs)
            if diffs[min_diff] <= windows[i] // 4:
                ridge[i] = extrema[min_diff]
                extrema[min_diff] = -1  # Skip later

        remaining_extrema = extrema[extrema > -1]
        if remaining_extrema.size != 0:
            new_ridges = np.full(
                (remaining_extrema.shape[0], cwt_coef.shape[0]), -1, dtype=int
            )
            new_ridges[:, i] = remaining_extrema
            ridges = np.vstack((ridges, new_ridges))

    return ridges.T


def _filter_ridges(
    ridges: np.ndarray,
    cwt_coef: np.ndarray,
    noise_window: int = None,
    min_noise: float = None,
    min_snr: float = 10.0,
    min_length: int = None,
) -> np.ndarray:
    if noise_window is None:
        noise_window = cwt_coef.shape[1] // 10
    if min_noise is None:
        min_noise = np.amax(np.abs(cwt_coef[0])) / 100.0
    if min_length is None:
        min_length = ridges.shape[0] // 3

    # Trim ridges that are to short
    ridge_lengths = np.count_nonzero(ridges > -1, axis=0)
    ridges = ridges[:, ridge_lengths > min_length]

    # Build array of ridge values, filter out non valid ridges
    values = np.take_along_axis(cwt_coef, ridges, axis=1)
    max_rows = np.nanargmax(np.where(ridges > -1, values, np.nan), axis=0)
    max_cols = np.take_along_axis(  # This is gross
        ridges, max_rows.reshape(-1, *max_rows.shape), axis=0
    )[0]
    max_coords = np.vstack((max_rows, max_cols))

    windows = sliding_window_centered(cwt_coef[0], noise_window, 1)
    noises = np.nanpercentile(np.abs(windows), 10, axis=1)
    noises[np.logical_or(noises < min_noise, np.isnan(noises))] = min_noise

    snrs = cwt_coef[max_coords[0], max_coords[1]] / noises[max_coords[1]]

    return ridges[:, snrs > min_snr], max_coords[:, snrs > min_snr]


def _peak_data_from_ridges(
    x: np.ndarray,
    ridges: np.ndarray,
    maxima_coords: np.ndarray,
    cwt_windows: np.ndarray,
    peak_height_method: str = "maxima",
    peak_integration_method: str = "base",
) -> np.ndarray:
    widths = np.take(cwt_windows, maxima_coords[0])

    lefts = maxima_coords[1] - widths
    rights = maxima_coords[1] + widths
    bases = np.minimum(lefts, rights)

    if peak_height_method == "cwt":  # Height at maxima cwt ridge
        tops = maxima_coords[1]
    elif peak_height_method == "maxima":  # Max data height inside peak width
        ranges = np.vstack((lefts, rights)).T
        # PYTHON LOOP HERE
        tops = np.array([np.argmax(x[r[0] : r[1]]) + r[0] for r in ranges])
    else:
        raise ValueError("Valid peak_height_method are 'cwt', 'maxima'.")

    if peak_integration_method == "base":
        area = np.array(
            [np.trapz(x[r[0] : r[1]] - x[bases[i]]) for i, r in enumerate(ranges)]
        )
    elif peak_integration_method == "prominence":
        prominences = np.maximum(x[lefts], x[rights])
        area = np.array(
            [np.trapz(x[r[0] : r[1]] - prominences[i]) for i, r in enumerate(ranges)]
        )
    else:
        raise ValueError("Valid peak_integration_method are 'base', 'prominence'.")

    dtype = np.dtype(
        {
            "names": ["height", "width", "area", "top", "base", "left", "right"],
            "formats": [float, float, float, int, int, int, int],
        }
    )
    peaks = np.empty(tops.shape, dtype=dtype)
    peaks["area"] = area
    peaks["height"] = x[tops] - x[bases]
    peaks["width"] = widths
    peaks["top"] = tops
    peaks["base"] = bases
    peaks["left"] = lefts
    peaks["right"] = rights
    return peaks


def find_peaks(
    x: np.ndarray,
    min_midth: int,
    max_width: int,
    ridge_gap_threshold: int = None,
    ridge_min_snr: float = 10.0,
    peak_integration_method: str = "base",
    peak_min_area: float = 0.0,
    peak_min_height: float = 0.0,
    peak_min_width: float = 0.0,
    peak_min_prominence: float = 0.0,
) -> np.ndarray:

    windows = np.arange(min_midth, max_width + 1)
    cwt_coef = cwt(x, windows, ricker_wavelet)
    ridges = _identify_ridges(cwt_coef, windows, gap_threshold=ridge_gap_threshold)
    ridges, ridge_maxima = _filter_ridges(ridges, cwt_coef, min_snr=ridge_min_snr)

    peaks = _peak_data_from_ridges(
        x,
        ridges,
        ridge_maxima,
        windows,
        peak_height_method="maxima",
        peak_integration_method=peak_integration_method,
    )

    # Filter the peaks based on final criteria
    bad_area = peaks["area"] < peak_min_area
    bad_heights = peaks["height"] < peak_min_height
    bad_widths = peaks["width"] < peak_min_width
    bad_prominences = (
        peaks["height"] - np.maximum(x[peaks["left"]], x[peaks["right"]])
        < peak_min_prominence
    )
    bad_peaks = np.logical_or.reduce(
        (bad_area, bad_heights, bad_widths, bad_prominences)
    )

    return peaks[~bad_peaks]