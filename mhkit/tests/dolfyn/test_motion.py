from . import test_read_adv as tv
from .base import load_netcdf as load, save_netcdf as save, assert_allclose, drop_config
from mhkit.dolfyn.adv import api
from mhkit.dolfyn.io.api import read_example as read
import unittest

make_data = False


class mc_testcase(unittest.TestCase):
    def test_motion_adv(self):
        tdm = tv.dat_imu.copy(deep=True)
        tdm = api.correct_motion(tdm)

        # user added metadata
        tdmj = tv.dat_imu_json.copy(deep=True)
        tdmj = api.correct_motion(tdmj)

        # set declination and then correct
        tdm10 = tv.dat_imu.copy(deep=True)
        tdm10.velds.set_declination(10.0, inplace=True)
        tdm10 = api.correct_motion(tdm10)

        # test setting declination to 0 doesn't affect correction
        tdm0 = tv.dat_imu.copy(deep=True)
        tdm0.velds.set_declination(0.0, inplace=True)
        tdm0 = api.correct_motion(tdm0)
        tdm0.attrs.pop('declination')
        tdm0.attrs.pop('declination_in_orientmat')

        # test motion-corrected data rotation
        tdmE = tv.dat_imu.copy(deep=True)
        tdmE.velds.set_declination(10.0, inplace=True)
        tdmE.velds.rotate2('earth', inplace=True)
        tdmE = api.correct_motion(tdmE)

        # ensure trailing nans are removed from AHRS data
        ahrs = drop_config(read(
            'vector_data_imu01.VEC', userdata=True))
        for var in ['accel', 'angrt', 'mag']:
            assert not ahrs[var].isnull().any(
            ), "nan's in {} variable".format(var)

        if make_data:
            save(tdm, 'vector_data_imu01_mc.nc')
            save(tdm10, 'vector_data_imu01_mcDeclin10.nc')
            save(tdmj, 'vector_data_imu01-json_mc.nc')
            return

        cdm10 = load('vector_data_imu01_mcDeclin10.nc')

        assert_allclose(tdm, load('vector_data_imu01_mc.nc'), atol=1e-7)
        assert_allclose(tdm10, tdmj, atol=1e-7)
        assert_allclose(tdm0, tdm, atol=1e-7)
        assert_allclose(tdm10, cdm10, atol=1e-7)
        assert_allclose(tdmE, cdm10, atol=1e-7)
        assert_allclose(tdmj, load('vector_data_imu01-json_mc.nc'), atol=1e-7)

    def test_sep_probes(self):
        tdm = tv.dat_imu.copy(deep=True)
        tdm = api.correct_motion(tdm, separate_probes=True)

        if make_data:
            save(tdm, 'vector_data_imu01_mcsp.nc')
            return

        assert_allclose(tdm, load('vector_data_imu01_mcsp.nc'), atol=1e-7)
