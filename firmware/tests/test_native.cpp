#include "protocol.h"
#include "safety.h"
#include "control_loop.h"
#include "motors.h"
#include "config.h"
#include "command_receiver.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static HostCommand command(uint8_t id=CMD_SETPOINT) {
  HostCommand c={};
  c.magic=PROTOCOL_MAGIC;c.version=PROTOCOL_VERSION;c.size=sizeof(c);
  c.sequence=0xfffffffeu;c.timestamp_us=123456789;c.cmd_id=id;
  return c;
}
static void crc(HostCommand&c){
  c.crc16=protocol_crc16(reinterpret_cast<const uint8_t*>(&c),sizeof(c)-2);
}
static bool feed(CommandParser&p,const HostCommand&c,HostCommand&out,uint32_t time=0){
  bool parsed=false;
  const uint8_t*bytes=reinterpret_cast<const uint8_t*>(&c);
  for(unsigned i=0;i<sizeof(c);++i)parsed=p.feed(bytes[i],time,out)||parsed;
  return parsed;
}
static void hex(const void*p,unsigned n){
  const uint8_t*b=reinterpret_cast<const uint8_t*>(p);
  for(unsigned i=0;i<n;++i)printf("%02x",b[i]);
  printf("\n");
}
static void send(CommandReceiver &receiver, HostCommand c, uint32_t now_ms,
                 bool corrupt_crc=false) {
  crc(c);
  if(corrupt_crc)c.crc16^=1;
  const uint8_t*bytes=reinterpret_cast<const uint8_t*>(&c);
  for(unsigned i=0;i<sizeof(c);++i)receiver.feed(bytes[i],now_ms);
  // Every actual dispatch path must preserve the production qualification lock.
  assert(safety_faults()&FLT_UNQUALIFIED);
  assert(safety_state()==RobotState::Fault);
  assert(!safety_motion_allowed());
}
static void test_production_dispatcher() {
  safety_init();control_init();
  CommandReceiver receiver;
  assert(!safety_status().have_host);
  HostCommand c=command(CMD_NOP);c.sequence=100;
  send(receiver,c,10);
  assert(safety_status().have_host&&safety_status().last_host_ms==10);
  send(receiver,c,20); // duplicate
  c.sequence=99;send(receiver,c,30); // stale
  assert(safety_status().last_host_ms==10);
  c.sequence=101;send(receiver,c,40,true); // damaged CRC cannot renew freshness
  assert(safety_status().last_host_ms==10);
  c.flags=1;send(receiver,c,41);
  assert(safety_status().last_host_ms==10);
  c.flags=0;send(receiver,c,42); // rejected sequence 101 was not consumed
  assert(safety_status().last_host_ms==42);

  c=command(CMD_ENABLE);c.sequence=102;send(receiver,c,50);
  assert(safety_status().last_host_ms==50);
  c=command(CMD_CLEAR_FLT);c.sequence=103;send(receiver,c,51);
  assert(safety_status().last_host_ms==51);
  const uint8_t unsupported_commands[]={CMD_HOME,CMD_TRAJ};
  for(uint8_t unsupported: unsupported_commands) {
    c=command(unsupported);c.sequence=104;send(receiver,c,52);
    assert(safety_status().last_host_ms==51);
  }
  c=command(CMD_SETPOINT);c.sequence=104;c.latch=1;send(receiver,c,53);
  assert(safety_status().last_host_ms==51);
  c.latch=0;c.yaw_mdeg=70001;send(receiver,c,54);
  assert(safety_status().last_host_ms==51);
  c.yaw_mdeg=70000;c.pitch_mdeg=70000;c.extension_mm=500;send(receiver,c,55);
  assert(safety_status().last_host_ms==55);
  assert(safety_status().last_setpoint_ms==0);
  assert(!control_axis(0).target_valid); // no command retained while disarmed

  // Nonzero stale state is introduced only into the math scaffold, never safety.
  control_set_targets({50,40,300,0,0,0});control_update_measurement(0,10,0,0);
  c=command(CMD_DISABLE);c.sequence=1;send(receiver,c,56);
  assert(safety_status().last_host_ms==55);
  assert(!control_axis(0).target_valid&&!control_axis(0).measurement_valid);
  assert(control_axis(0).target==0&&isnan(control_axis(0).pos));
  c=command(CMD_RESET_LINK);c.sequence=2;send(receiver,c,57);
  assert(safety_status().last_host_ms==55); // reset-link is not a heartbeat
  c=command(CMD_NOP);c.sequence=2;send(receiver,c,58);
  assert(safety_status().last_host_ms==55); // equal reset sequence is a replay
  c.sequence=3;send(receiver,c,59);assert(safety_status().last_host_ms==59);
  c=command(CMD_RESET_LINK);c.sequence=0xfffffffeu;send(receiver,c,60);
  c=command(CMD_NOP);c.sequence=0xffffffffu;send(receiver,c,61);
  c.sequence=0;send(receiver,c,62);assert(safety_status().last_host_ms==62);
  c.sequence=0xffffffffu;send(receiver,c,63);assert(safety_status().last_host_ms==62);
  c.sequence=0x80000000u;send(receiver,c,64);assert(safety_status().last_host_ms==62);

  // A truncated frame and its timeout use the SAME feed path called from loop().
  c=command(CMD_NOP);c.sequence=1;crc(c);
  const uint8_t *bytes=reinterpret_cast<const uint8_t*>(&c);
  for(unsigned i=0;i<10;++i)receiver.feed(bytes[i],65);
  assert(safety_status().last_host_ms==62);
  send(receiver,c,100);
  assert(safety_status().last_host_ms==100);
  c.sequence=2;crc(c);bytes=reinterpret_cast<const uint8_t*>(&c);
  for(unsigned i=0;i<sizeof(c);++i)if(i!=17)receiver.feed(bytes[i],101);
  assert(safety_status().last_host_ms==100);
  send(receiver,c,102);assert(safety_status().last_host_ms==102);
  assert(safety_faults()&FLT_PROTOCOL);

  // A fresh production boot still cannot be enabled or cleared.
  safety_init();control_init();CommandReceiver rebooted;
  c=command(CMD_ENABLE);c.sequence=0;send(rebooted,c,0);
  c=command(CMD_CLEAR_FLT);c.sequence=1;send(rebooted,c,1);
  assert(!control_axis(0).target_valid&&!control_axis(0).measurement_valid);
}
int main(int argc,char**argv){
  HostCommand c=command();c.yaw_mdeg=-70000;c.pitch_mdeg=70000;
  c.extension_mm=500;c.yaw_vel_mdeg_s=-20000;c.pitch_vel_mdeg_s=20000;c.ext_vel_mm_s=-150;crc(c);
  if(argc==2 && !strcmp(argv[1],"--wire")){
    hex(&c,sizeof(c));
    TelemetryFrame t={};
    t.magic=PROTOCOL_MAGIC;t.version=PROTOCOL_VERSION;t.size=sizeof(t);t.timestamp_us=123456789;
    t.status=5;t.catch_sensor=255;t.yaw_mdeg=-70000;t.pitch_mdeg=70000;t.extension_mm=500;
    t.yaw_vel_mdeg_s=-20000;t.pitch_vel_mdeg_s=20000;t.ext_vel_mm_s=-150;
    t.yaw_target_mdeg=-69000;t.pitch_target_mdeg=69000;t.ext_target_mm=499;
    t.current_yaw_mA=INT32_MIN;t.current_pitch_mA=2300;t.current_ext_mA=-100;
    t.fault_bits=FLT_UNQUALIFIED;t.crc16=protocol_crc16(reinterpret_cast<const uint8_t*>(&t),sizeof(t)-2);
    hex(&t,sizeof(t));return 0;
  }
  assert(protocol_crc16(reinterpret_cast<const uint8_t*>("123456789"),9)==0x4b37);
  assert(protocol_sequence_newer(0,0xffffffffu));
  assert(!protocol_sequence_newer(5,5));
  assert(!protocol_sequence_newer(4,5));
  assert(!protocol_sequence_newer(0x80000000u,0));
  assert(protocol_validate_command(c)==FLT_NONE);
  HostCommand bad=c;bad.yaw_mdeg=INT32_MIN;crc(bad);
  assert(protocol_validate_command(bad)==FLT_WORKSPACE);
  bad=c;bad.ext_vel_mm_s=151;crc(bad);assert(protocol_validate_command(bad)==FLT_WORKSPACE);
  bad=c;bad.latch=1;crc(bad);assert(protocol_validate_command(bad)==FLT_PROTOCOL);
  bad=command(CMD_HOME);crc(bad);assert(protocol_validate_command(bad)==FLT_UNQUALIFIED);
  bad=command(CMD_ENABLE);bad.extension_mm=1;crc(bad);
  assert(protocol_validate_command(bad)==FLT_PROTOCOL);
  CommandParser parser;HostCommand out;
  assert(feed(parser,c,out));assert(out.yaw_mdeg==-70000);
  bad=c;bad.pitch_mdeg=0; // invalid CRC
  assert(!feed(parser,bad,out));assert(parser.errors());
  assert(feed(parser,c,out)); // recover after corrupt frame
  parser.feed(0x17,0,out);parser.feed(0xa5,0,out);parser.feed(0xa5,0,out);
  assert(feed(parser,c,out)); // noise, repeated sync byte, following frame
  CommandParser partial;
  const uint8_t*bytes=reinterpret_cast<const uint8_t*>(&c);
  for(unsigned i=0;i<12;++i)partial.feed(bytes[i],0xfffffff0u,out);
  assert(feed(partial,c,out,20));assert(partial.errors()); // timeout across millis wrap
  // Dropped byte must not permanently shift framing.
  CommandParser dropped;
  for(unsigned i=0;i<sizeof(c);++i)if(i!=17)dropped.feed(bytes[i],0,out);
  assert(feed(dropped,c,out));
  // Qualification lock cannot be cleared by any available API.
  safety_init();assert(!safety_motion_allowed());
  SafetyInputs inputs;inputs.estop_open=inputs.home_open=inputs.max_open=false;
  inputs.feedback_valid=inputs.current_valid=true;
  safety_tick(0,inputs);safety_note_host(0);safety_clear_if_safe();
  assert(safety_faults()&FLT_UNQUALIFIED);assert(!safety_motion_allowed());
  safety_disable();assert(safety_state()==RobotState::Fault);
  inputs.estop_open=true;safety_tick(1,inputs);assert(safety_faults()&FLT_ESTOP);
  inputs.home_open=inputs.max_open=true;safety_tick(2,inputs);assert(safety_faults()&FLT_LIMIT);
  float p,v,i;motors_read_state(0,&p,&v,&i);assert(isnan(p)&&isnan(v)&&isnan(i));
  control_init();control_set_targets({70,70,500,20,20,150});
  control_update_measurement(0,0,0,0);control_step(.001f);
  assert(control_effort(0)==0); // unidentified plant starts at zero gains
  control_set_gains(0,1,0,1);
  for(int n=0;n<1000;++n)control_step(.001f);
  assert(control_effort(0)==1);assert(control_axis(0).integral==0); // anti-windup
  control_update_measurement(0,NAN,0,0);control_step(.001f);assert(control_effort(0)==0);
  control_reset();assert(control_effort(1)==0);
  assert(!control_axis(0).target_valid&&!control_axis(0).measurement_valid);
  assert(control_axis(0).target==0&&isnan(control_axis(0).pos));
  control_update_measurement(0,0,0,0);control_step(.001f);
  assert(control_effort(0)==0); // valid feedback alone cannot replay prior target
  test_production_dispatcher();
  printf("native protocol, production dispatcher, qualification lock and controller tests passed\n");
}
