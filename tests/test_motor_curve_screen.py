"""The supplier graph screen cannot become voltage/thermal qualification."""
import unittest
from engineering.ratio_trade_study import graph_lower_screen, run


class MotorGraphTests(unittest.TestCase):
    def test_speed_uncertainty_uses_both_segments_without_extrapolation(self):
        curve=dict(points_rpm_nm=[[100,2],[200,1.5],[300,1]],
                   rpm_reading_allowance=10,torque_reading_allowance_nm=.05)
        self.assertIsNone(graph_lower_screen(100,curve))
        self.assertIsNone(graph_lower_screen(300,curve))
        self.assertAlmostEqual(graph_lower_screen(200,curve),.95)

    def test_promising_ratio_does_not_qualify_motor_or_24v_supply(self):
        result=run()
        self.assertEqual(result['curve_source']['bus_voltage_v'],48)
        self.assertTrue(any(r['passes_48v_graph_screen'] for r in result['results']))
        self.assertTrue(all(not r['qualified'] for r in result['results']))
        baseline=[r for r in result['results'] if (r['axis'],r['ratio']) in [('pitch',8),('yaw',6)]]
        self.assertTrue(all(not r['passes_48v_graph_screen'] for r in baseline))


if __name__=='__main__':unittest.main()
