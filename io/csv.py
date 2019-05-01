import numpy as np

from .. import __version__, Laser, LaserCalibration, LaserConfig, LaserData
from .error import LaserLibException

from typing import Dict, TextIO, Tuple, Union


def load(fp: Union[str, TextIO]) -> np.ndarray:
    if isinstance(fp, str):
        fp = open(fp, "rb")

    try:
        cleaned = (line.replace(b";", b",").replace(b"\t", b",") for line in fp)
        data = np.genfromtxt(cleaned, delimiter=b",", comments=b"#", dtype=float)
    except ValueError as e:
        raise LaserLibException("Could not parse file.") from e

    if data.ndim != 2:
        raise LaserLibException(f"Invalid data dimensions '{data.ndim}'.")

    data.dtype = ("_", data.dtype)
    return data


def load_header(fp: Union[str, TextIO]) -> Tuple[str, LaserConfig, LaserCalibration]:
    def string_to_dict(s: str, delim: str = ";", kvsep: str = "=") -> Dict[str, str]:
        tokens = s.split(delim)
        return {k: v for k, v in [token.split(kvsep) for token in tokens]}

    if isinstance(fp, str):
        fp = open(fp, "rb")

    line = fp.readline().lstrip(b"#").strip()
    if not line.startswith(b"Pew Pew "):  # CSV generated by pewpew
        raise LaserLibException("Missing header!")
    # Version
    version = line[8:]
    if version < b"0.1.1":
        raise LaserLibException(f"Unsupported CSV version '{version}'.")
    # Isotope
    line = fp.readline().lstrip(b"#").strip()
    if b"=" not in line:
        raise LaserLibException(f"Malformed isotope line '{line}'.")
    tokens = line.split(b"=")
    if tokens[0] != b"isotope":
        raise LaserLibException(f"Malformed isotope line '{line}'.")
    isotope = tokens[1].decode()
    # Config
    line = fp.readline().lstrip(b"#").strip()
    try:
        config_dict = string_to_dict(line.decode())
        config = LaserConfig(
            spotsize=float(config_dict["spotsize"]),
            speed=float(config_dict["speed"]),
            scantime=float(config_dict["scantime"]),
        )
    except (KeyError, ValueError):
        raise LaserLibException(f"Malformed config line '{line}'.")
    # Calibration
    try:
        line = fp.readline().lstrip(b"#").strip()
        cal_dict = string_to_dict(line.decode())
        calibration = LaserCalibration(
            intercept=float(cal_dict["intercept"]),
            gradient=float(cal_dict["gradient"]),
            unit=cal_dict["unit"],
        )
    except (KeyError, ValueError):
        raise LaserLibException(f"Malformed calibration line '{line}'")

    return isotope, config, calibration


def save(path: str, data: np.ndarray, header: str = "") -> None:
    np.savetxt(path, data, fmt="%g", delimiter=",", comments="#", header=header)


def make_header(laser: Laser, isotope: str) -> str:
    return (
        f"Laserlib {__version__}\nisotope={isotope}\n"
        f"spotsize={laser.config.spotsize};speed={laser.config.speed};"
        f"scantime={laser.config.scantime}\n"
        f"intercept={laser.data[isotope].calibration.intercept};"
        f"gradient={laser.data[isotope].calibration.gradient};"
        f"unit={laser.data[isotope].calibration.unit}\n"
    )
