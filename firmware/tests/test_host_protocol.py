"""Run from repository root: python -m unittest discover -s firmware/tests -v."""
import math
import os
import struct
import subprocess
import time
import unittest

from host.control.serial_bridge import (
    COMMAND, TELEMETRY, INVALID, MAGIC, VERSION, ArmController, CommandId,
    Setpoint, TelemetryParser, crc16, decode_telemetry, pack_command,
    pack_setpoint, sequence_newer,
)

def telemetry_bytes(timestamp=123, state=5, faults=256):
    raw=TELEMETRY.pack(MAGIC,VERSION,TELEMETRY.size,timestamp,state,255,
                       *([INVALID]*6),0,0,0,*([INVALID]*3),faults,0)
    return raw[:-2]+struct.pack("<H",crc16(raw[:-2]))

class ProtocolTests(unittest.TestCase):
    def test_crc_reference(self):
        self.assertEqual(crc16(b"123456789"),0x4B37)

    def test_full_angular_range(self):
        raw=pack_setpoint(Setpoint(-70,70,500,-20,20,-150),123456789,sequence=0xFFFFFFFE)
        fields=COMMAND.unpack(raw)
        self.assertEqual(len(raw),44)
        self.assertEqual(fields[7:13],(-70000,70000,500,-20000,20000,-150))
        self.assertEqual(crc16(raw[:-2]),fields[-1])

    def test_bad_commands(self):
        for bad in (Setpoint(math.nan,0,0),Setpoint(71,0,0),Setpoint(0,0,501),
                    Setpoint(0,0,0,21),Setpoint(0,0,0,ext_vel=151),Setpoint(0,0,0,latch=1)):
            with self.assertRaises(ValueError):pack_setpoint(bad)
        for cmd in (CommandId.HOME,CommandId.TRAJ):
            with self.assertRaises(ValueError):pack_command(cmd,sequence=0)
        with self.assertRaises(ValueError):pack_setpoint(Setpoint(1,0,0),cmd_id=CommandId.ENABLE)
        with self.assertRaises(ValueError):pack_command(CommandId.DISABLE,sequence=-1)

    def test_rollover(self):
        self.assertTrue(sequence_newer(0,0xFFFFFFFF))
        self.assertFalse(sequence_newer(1,1))
        self.assertFalse(sequence_newer(0,1))

    def test_missing_measurements(self):
        tlm=decode_telemetry(telemetry_bytes(),received_at=1)
        self.assertIsNone(tlm.catch_sensor)
        self.assertEqual(tlm.positions,(None,None,None))
        self.assertFalse(tlm.feedback_valid)
        self.assertEqual(tlm.faults,256)

    def test_parser_noise_corruption_drop_timeout(self):
        frame=telemetry_bytes()
        parser=TelemetryParser()
        corrupt=bytearray(frame);corrupt[15]^=1
        self.assertEqual(len(parser.feed(b"noise"+corrupt+frame,now=0)),1)
        self.assertGreater(parser.errors,0)
        self.assertEqual(len(parser.feed(frame[:10],now=0.01)),0)
        self.assertEqual(len(parser.feed(frame,now=0.04)),1)
        self.assertEqual(len(parser.feed(frame[:25]+frame[26:]+frame,now=0.05)),1)
        self.assertLess(len(parser.buffer),62)

    def test_fail_closed_host(self):
        ctrl=ArmController()
        with self.assertRaises(ConnectionError):ctrl.send_setpoint(Setpoint(0,0,0))
        class FakeSerial:
            in_waiting=62
            def read(self,n):return telemetry_bytes()
            def write(self,data):raise AssertionError("Unqualified telemetry must never permit write")
        ctrl.ser=FakeSerial()
        with self.assertRaises(RuntimeError):ctrl.send_setpoint(Setpoint(0,0,0))
        received=ctrl.telemetry.received_at
        ctrl.poll()
        self.assertEqual(ctrl.telemetry.received_at,received) # duplicate cannot refresh

    @unittest.skipUnless(os.environ.get("VRA_NATIVE_TEST_BINARY"),"native binary not configured")
    def test_cross_language_wire(self):
        lines=subprocess.check_output([os.environ["VRA_NATIVE_TEST_BINARY"],"--wire"],text=True).splitlines()
        self.assertEqual(bytes.fromhex(lines[0]),pack_setpoint(
            Setpoint(-70,70,500,-20,20,-150),123456789,sequence=0xFFFFFFFE))
        tlm=decode_telemetry(bytes.fromhex(lines[1]))
        self.assertEqual(tlm.positions,(-70,70,500))
        self.assertEqual(tlm.velocities,(-20,20,-150))
        self.assertEqual(tlm.current_mA,(None,2300,-100))
        self.assertEqual(tlm.targets,(-69,69,499))

if __name__=="__main__":unittest.main()
