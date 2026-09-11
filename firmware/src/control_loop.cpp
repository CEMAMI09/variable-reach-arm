#include "control_loop.h"
#include "config.h"
#include <math.h>
static AxisState axes[NUM_AXES];
static float effort[NUM_AXES];
static bool valid_axis(int axis) { return axis>=0 && axis<NUM_AXES; }
static float bound(float v,float lo,float hi) { return v<lo?lo:(v>hi?hi:v); }
void control_init() {
  // Plant and driver effort units are unidentified. Zero gains prevent a false tuned controller.
  for(int i=0;i<NUM_AXES;++i){axes[i]={};effort[i]=0;}
  control_reset();
}
void control_reset(){
  for(int i=0;i<NUM_AXES;++i){
    AxisState &a=axes[i];
    a.integral=0;a.target=0;a.target_vel=0;
    a.pos=NAN;a.vel=NAN;a.current_mA=NAN;
    a.target_valid=false;a.measurement_valid=false;effort[i]=0;
  }
}
void control_set_gains(int axis,float kp,float kd,float ki){
  if(!valid_axis(axis) || !isfinite(kp) || !isfinite(kd) || !isfinite(ki) ||
      kp<0 || kd<0 || ki<0)return;
  axes[axis].kp=kp;axes[axis].kd=kd;axes[axis].ki=ki;
}
void control_set_targets(const JointCommand&c){
  const float pos[3]={c.yaw_deg,c.pitch_deg,c.ext_mm};
  const float vel[3]={c.yaw_vel,c.pitch_vel,c.ext_vel};
  for(int i=0;i<3;++i)if(!isfinite(pos[i])||!isfinite(vel[i])){control_reset();return;}
  for(int i=0;i<3;++i){axes[i].target=pos[i];axes[i].target_vel=vel[i];axes[i].target_valid=true;}
}
void control_update_measurement(int axis,float pos,float vel,float current){
  if(!valid_axis(axis))return;
  axes[axis].pos=pos;axes[axis].vel=vel;axes[axis].current_mA=current;
  axes[axis].measurement_valid=isfinite(pos)&&isfinite(vel)&&isfinite(current);
}
void control_step(float dt){
  if(!isfinite(dt)||dt<=0||dt>WATCHDOG_MS*.001f){control_reset();return;}
  for(int i=0;i<NUM_AXES;++i){
    AxisState&a=axes[i];
    if(!a.target_valid||!a.measurement_valid||
        !isfinite(a.pos)||!isfinite(a.vel)||!isfinite(a.current_mA)){
      effort[i]=0;a.integral=0;continue;
    }
    float e=a.target-a.pos,de=a.target_vel-a.vel;
    float pd=a.kp*e+a.kd*de;
    float integral=a.ki>0?bound(a.integral+e*dt,-1.f/a.ki,1.f/a.ki):0;
    float trial=pd+a.ki*integral;
    if((trial<=1 && trial>=-1)||(trial>1 && e<0)||(trial< -1 && e>0))
      a.integral=integral; // conditional integration anti-windup
    effort[i]=bound(pd+a.ki*a.integral,-1,1);
    if(!isfinite(effort[i]))effort[i]=0;
  }
}
float control_effort(int axis){return valid_axis(axis)?effort[axis]:0;}
const AxisState&control_axis(int axis){return axes[valid_axis(axis)?axis:0];}
